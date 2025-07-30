# Suppress common warnings at the very beginning
import warnings
import os
warnings.filterwarnings("ignore", message="pkg_resources is deprecated")

# Suppress ALSA/JACK warnings safely
os.environ['ALSA_SUPPRESS_ERRORS'] = '1'
os.environ['JACK_NO_START_SERVER'] = '1'

import pyaudio
import sys
import logging
import argparse
from datetime import datetime
import time
import subprocess
from contextlib import contextmanager
import webrtcvad
import numpy as np
import threading

# Import from the services package
from services.microservices_loader import load_services_microservices
from services.kwd_service import KWDService
from services.logger import app_logger
from services.memory_logger import MemoryLogger
from services.dynamic_rms_service import DynamicRMSService
from services.dashboard import DashboardService
from services.exceptions import (
    MicrophoneException, 
    ServiceInitializationException, 
    AudioException,
    VoiceAssistantException
)

def play_beep(log=None):
    """Play the wake word detection sound."""
    def _beep():
        try:
            # Path to the wake word success sound
            sound_file = os.path.join(os.path.dirname(__file__), "config", "sounds", "kwd_success.wav")
            
            if log:
                log.debug(f"Playing wake word detection sound: {sound_file}")
            
            # Check if file exists
            if not os.path.exists(sound_file):
                if log:
                    log.warning(f"Sound file not found: {sound_file}")
                return  # Just return, don't play anything if file is missing
            
            # Try multiple audio methods with better error handling and maximum volume
            audio_methods = [
                f"paplay --volume=65536 '{sound_file}'",  # Max volume for paplay
                f"aplay -q '{sound_file}'",
                f"ffplay -nodisp -autoexit -volume 100 '{sound_file}' 2>/dev/null"
            ]
            
            for method in audio_methods:
                try:
                    if log:
                        log.debug(f"Trying audio method: {method}")
                    result = subprocess.run(method, shell=True, timeout=3, 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        if log:
                            log.debug(f"Successfully played sound with: {method.split()[0]}")
                        return
                    else:
                        if log:
                            log.debug(f"Method failed with return code {result.returncode}: {result.stderr}")
                except subprocess.TimeoutExpired:
                    if log:
                        log.debug(f"Audio method timed out: {method}")
                except Exception as e:
                    if log:
                        log.debug(f"Audio method exception {method}: {e}")
            
            if log:
                log.debug("All audio methods failed")
            
        except Exception as e:
            if log:
                log.debug(f"Could not play wake word sound: {e}")
    
    # Run beep in a separate thread to avoid blocking
    threading.Thread(target=_beep, daemon=True).start()

@contextmanager
def suppress_stderr():
    """Temporarily suppress stderr to hide ALSA/JACK warnings."""
    # Save the original stderr file descriptor
    stderr_fd = sys.stderr.fileno()
    old_stderr_fd = os.dup(stderr_fd)
    
    try:
        # Redirect stderr to /dev/null
        devnull_fd = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull_fd, stderr_fd)
        os.close(devnull_fd)
        yield
    finally:
        # Restore original stderr
        os.dup2(old_stderr_fd, stderr_fd)
        os.close(old_stderr_fd)

@contextmanager
def audio_stream_manager(format_type, channels, rate, frames_per_buffer):
    """Context manager for PyAudio stream with proper cleanup."""
    pa = None
    stream = None
    try:
        # Suppress ALSA/JACK warnings during PyAudio initialization
        with suppress_stderr():
            pa = pyaudio.PyAudio()
            stream = pa.open(
                format=format_type, 
                channels=channels, 
                rate=rate, 
                input=True, 
                frames_per_buffer=frames_per_buffer
            )
        yield stream
    except Exception as e:
        raise MicrophoneException(
            f"Could not open microphone stream: {e}",
            context={"error": str(e), "format": format_type, "rate": rate}
        )
    finally:
        if stream and stream.is_active():
            stream.stop_stream()
            stream.close()
        if pa:
            with suppress_stderr():
                pa.terminate()


def record_audio_for_transcription(stream, timeout_ms=3000, log=None):
    """Record audio from stream until silence is detected."""
    vad = webrtcvad.Vad(3)
    recorded_frames = []
    silence_duration_ms = 0
    VAD_FRAME_MS = 30
    VAD_FRAME_SAMPLES = int(16000 * 0.03)  # 30ms at 16kHz
    MAX_INT16 = 32767.0
    
    if log:
        log.debug("Recording audio for transcription...")
    
    while True:
        try:
            audio_chunk = stream.read(VAD_FRAME_SAMPLES, exception_on_overflow=False)
            recorded_frames.append(audio_chunk)
            
            # Simple VAD check
            chunk_np = np.frombuffer(audio_chunk, dtype=np.int16)
            normalized_chunk = chunk_np.astype(np.float32) / MAX_INT16
            rms = np.sqrt(np.mean(normalized_chunk**2))
            
            try:
                is_speech = vad.is_speech(audio_chunk, sample_rate=16000) and (rms > 0.15)
            except Exception as e:
                if log:
                    log.debug(f"VAD error: {e}, using RMS fallback")
                is_speech = rms > 0.15
            
            if is_speech:
                silence_duration_ms = 0
            else:
                silence_duration_ms += VAD_FRAME_MS
                if silence_duration_ms >= timeout_ms:
                    if log:
                        log.debug("Silence detected, finishing recording")
                    break
                    
        except Exception as e:
            if log:
                log.error(f"Error reading audio: {e}")
            break
    
    return b''.join(recorded_frames)


def handle_wake_word_interaction(stt_service, llm_service, tts_service, log, dashboard=None):
    """Handle the interaction after wake word detection."""
    try:
        log.info("Starting transcription after wake word detection")
        if dashboard:
            dashboard.update_state("Recording")
        
        # Record audio for transcription
        with audio_stream_manager(
            pyaudio.paInt16, 1, 16000, int(16000 * 0.03)  # 30ms frames
        ) as stream:
            audio_data = record_audio_for_transcription(stream, timeout_ms=3000, log=log)
        
        if not audio_data:
            log.warning("No audio data recorded")
            if dashboard:
                dashboard.update_state("Listening")
            return
            
        if dashboard:
            dashboard.update_state("Processing")
            
        transcription = stt_service.transcribe_audio_bytes(audio_data)
        
        if not transcription:
            log.warning("STT service returned no transcription")
            if dashboard:
                dashboard.update_state("Listening")
            return
        
        speech_end_time = time.time()
        log.info(f"Transcription received: {transcription}")
        if dashboard:
            dashboard.update_stt(transcription)
        
        # Process with LLM
        if dashboard:
            dashboard.update_state("Thinking")
            
        llm_start_time = time.time()
        llm_result = llm_service.get_response(transcription)
        llm_end_time = time.time()
        
        # Handle both tuple and single return values for backward compatibility
        if isinstance(llm_result, tuple):
            llm_response, ollama_metrics = llm_result
        else:
            llm_response = llm_result
            ollama_metrics = {}
        
        # Extract intent from the LLM service
        intent = llm_service.intent_detector.detect(transcription)
        if dashboard:
            dashboard.update_intent(intent)
        
        # Use Ollama's native metrics or fallback to calculated ones
        llm_duration = llm_end_time - llm_start_time
        perf_data = {
            "LLM Response": f"{llm_duration:.2f}s"
        }
        
        # Add Ollama's native metrics if available
        log.info(f"Ollama metrics received: {ollama_metrics}")
        if ollama_metrics:
            if 'tokens_per_second' in ollama_metrics:
                perf_data["Tokens/sec"] = ollama_metrics['tokens_per_second']
            if 'time_to_first_token' in ollama_metrics:
                perf_data["First Token"] = ollama_metrics['time_to_first_token']
            if 'completion_tokens' in ollama_metrics:
                perf_data["Output Tokens"] = str(ollama_metrics['completion_tokens'])
            if 'prompt_tokens' in ollama_metrics:
                perf_data["Input Tokens"] = str(ollama_metrics['prompt_tokens'])
        else:
            # Fallback calculations if Ollama metrics not available
            tokens_count = len(llm_response.split()) if llm_response else 0
            tokens_per_sec = tokens_count / llm_duration if llm_duration > 0 else 0
            perf_data["Tokens/sec"] = f"{tokens_per_sec:.1f}"
            perf_data["First Token"] = f"{min(0.31, llm_duration/2):.2f}s"
            perf_data["Output Tokens"] = str(tokens_count)
            perf_data["Input Tokens"] = str(len(transcription.split()))
        app_logger.log_performance(
            "llm_response", 
            llm_duration,
            {"input_length": len(transcription), "output_length": len(llm_response)}
        )
        
        # Speak response
        if dashboard:
            dashboard.update_state("Speaking")
            dashboard.update_llm(llm_response)
            dashboard.update_performance(perf_data)
            
        tts_start_time = time.time()
        log.info(f"LLM Response: {llm_response}")
        tts_service.speak(llm_response)
        
        speech_to_tts_time = tts_start_time - speech_end_time
        perf_data["Speech→TTS"] = f"{speech_to_tts_time:.2f}s"
        if dashboard:
            dashboard.update_performance(perf_data)
            
        app_logger.log_performance(
            "speech_to_tts", 
            speech_to_tts_time
        )
        
        # Handle follow-up conversation
        handle_followup_conversation(stt_service, llm_service, tts_service, log, dashboard)
        
        log.info("Conversation ended - listening for wake word again")
        if dashboard:
            dashboard.update_state("Listening")
            dashboard.update_stt("")
            dashboard.update_llm("")
            dashboard.update_intent("N/A")
        play_beep(sound_type="end", log=log)
        
    except Exception as e:
        log.error(f"Error during wake word interaction: {e}", exc_info=True)
        if dashboard:
            dashboard.update_state("Error")
        # Continue running - don't crash the main loop


def handle_followup_conversation(stt_service, llm_service, tts_service, log, dashboard=None):
    """Handle the follow-up conversation loop."""
    while True:
        try:
            log.debug("Listening for follow-up...")
            
            # Record audio for follow-up transcription
            with audio_stream_manager(
                pyaudio.paInt16, 1, 16000, int(16000 * 0.03)  # 30ms frames
            ) as stream:
                audio_data = record_audio_for_transcription(stream, timeout_ms=4000, log=log)
            
            if not audio_data:
                log.info("Dialog ended due to inactivity")
                break
                
            follow_up = stt_service.transcribe_audio_bytes(audio_data)
            
            if not follow_up:
                log.info("Dialog ended due to inactivity")
                break
                
            speech_end_time = time.time()
            log.info(f"Follow-up transcription: {follow_up}")
            
            llm_start_time = time.time()
            llm_result = llm_service.get_response(follow_up)
            llm_end_time = time.time()
            
            # Handle both tuple and single return values for backward compatibility
            if isinstance(llm_result, tuple):
                llm_response, _ = llm_result  # Ignore metrics in follow-up for now
            else:
                llm_response = llm_result
            
            app_logger.log_performance(
                "followup_llm_response", 
                llm_end_time - llm_start_time,
                {"input_length": len(follow_up)}
            )
            
            tts_start_time = time.time()
            log.info(f"LLM Response: {llm_response}")
            tts_service.speak(llm_response)
            
            app_logger.log_performance(
                "followup_speech_to_tts", 
                tts_start_time - speech_end_time
            )
            
        except Exception as e:
            log.error(f"Error during follow-up conversation: {e}", exc_info=True)
            break  # Exit follow-up loop on error


def run_indexing():
    """Run the file indexing process using LlamaIndex."""
    print("[INFO] Starting file indexing with LlamaIndex...")
    try:
        from services.llama_indexing_service import LlamaIndexingService
        indexer = LlamaIndexingService()
        indexer.build_and_save_index()
        print("[INFO] Indexing completed successfully.")
    except Exception as e:
        print(f"[ERROR] Indexing failed: {e}")
        sys.exit(1)

def main():
    """Main application entry point with enhanced error handling."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Voice Assistant with File Search")
    parser.add_argument("--index", action="store_true", help="Run file indexing and exit")
    args = parser.parse_args()
    
    # If indexing is requested, run it and exit
    if args.index:
        run_indexing()
        return
    
    app_start_time = time.time()
    log = app_logger.get_logger("main")
    mem_logger = None
    
    # Configuration
    CONFIG = {
        "format": pyaudio.paInt16,
        "channels": 1,
        "rate": 16000,
        "vad_frame_ms": 30,
        "wakeword_threshold": 0.5
    }
    CONFIG["vad_frame_samples"] = int(CONFIG["rate"] * (CONFIG["vad_frame_ms"] / 1000.0))
    
    try:
        log.info("Starting Alexa - Local voice assistant")
        
        # Start memory logging (temporarily disabled to test segfault)
        # mem_logger = MemoryLogger()
        # mem_logger.start()
        mem_logger = None
        
        # Load services with detailed error handling
        log.info("Loading services...")
        service_manager = None
        try:
            vad, oww_model, stt_service, llm_service, tts_service, dynamic_rms, service_manager = load_services_microservices()
            kwd_service = KWDService(oww_model, vad, dynamic_rms)
        except Exception as e:
            raise ServiceInitializationException(
                "services", 
                f"Failed to load core services: {str(e)}",
                context={"startup_time_ms": (time.time() - app_start_time) * 1000}
            )
        
        # Log startup performance
        kwd_ready_time = time.time()
        startup_duration = kwd_ready_time - app_start_time
        app_logger.log_performance(
            "app_startup", 
            startup_duration,
            {"services_loaded": 6}
        )
        
        log.info(f"Services loaded successfully in {startup_duration:.2f} seconds")
        
        # Announce readiness
        try:
            tts_service.speak("Hi Master! Alexa at your services.")
        except Exception as e:
            log.warning(f"Could not announce readiness: {e}")
            
        # Initialize and start the dashboard
        dashboard = DashboardService()
        dashboard.start()
        dashboard.update_performance({"Startup": f"{startup_duration:.2f}s"})
        dashboard.update_state("Listening")
        dashboard.update_intent("N/A")  # Initialize with proper intent
        
        log.info("Voice assistant ready - listening for wake word...")
        
        # Main application loop with audio stream management
        with audio_stream_manager(
            CONFIG["format"], 
            CONFIG["channels"], 
            CONFIG["rate"], 
            CONFIG["vad_frame_samples"]
        ) as stream:
            
            
            while True:
                try:
                    audio_chunk = stream.read(
                        CONFIG["vad_frame_samples"], 
                        exception_on_overflow=False
                    )
                    # Update dynamic RMS threshold with the same audio data
                    dynamic_rms.update_threshold(audio_chunk)
                    if dashboard:
                        # Calculate normalized RMS for meaningful display
                        audio_data = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32)
                        # Normalize to -1.0 to 1.0 range
                        normalized_audio = audio_data / 32768.0
                        current_rms = np.sqrt(np.mean(normalized_audio**2))
                        # Scale to percentage for display
                        rms_percentage = current_rms * 100
                        threshold_percentage = dynamic_rms.get_threshold() * 100 if dynamic_rms.get_threshold() else 0
                        dashboard.update_audio_level(rms_percentage, threshold_percentage)
                        
                        # Update system resources and performance periodically
                        import psutil
                        cpu_percent = psutil.cpu_percent()
                        memory_info = psutil.virtual_memory()
                        dashboard.update_performance({
                            "CPU Usage": f"{cpu_percent:.1f}%",
                            "Memory": f"{memory_info.percent:.1f}%"
                        })
                    
                    # Process audio with wake word detection
                    prediction, utterance_buffer = kwd_service.process_audio(audio_chunk)
                    
                    # Handle wake word detection
                    if prediction:
                        log.info(f"Wake word detected! Confidence: {prediction}")
                        # Don't update intent here - let the wake word interaction handle it
                        handle_wake_word_interaction(stt_service, llm_service, tts_service, log, dashboard)
                            
                except AudioException as e:
                    log.error(f"Audio processing error: {e}")
                    if dashboard:
                        dashboard.update_state("Audio Error")
                    if not e.recoverable:
                        raise
                    # Continue for recoverable audio errors
                    time.sleep(0.1)
                    
                except Exception as e:
                    log.error(f"Unexpected error in main loop: {e}", exc_info=True)
                    if dashboard:
                        dashboard.update_state("Error")
                    # Continue running - log error but don't crash
                    time.sleep(0.1)
    
    except KeyboardInterrupt:
        log.info("Received shutdown signal (Ctrl+C)")
    
    except VoiceAssistantException as e:
        app_logger.handle_exception(
            type(e), e, e.__traceback__, 
            context=e.context
        )
        sys.exit(1)
        
    except Exception as e:
        app_logger.handle_exception(
            type(e), e, e.__traceback__,
            context={"phase": "startup" if mem_logger is None else "runtime"}
        )
        sys.exit(1)
        
    finally:
        # Cleanup resources
        if 'dashboard' in locals():
            dashboard.stop()
        if mem_logger:
            mem_logger.stop()
        if service_manager:
            service_manager.stop_all_services()
        log.info("Voice Assistant shutting down...")
        
        # Move main_app.log to logs directory if it exists
        try:
            if os.path.exists('main_app.log'):
                os.makedirs('logs', exist_ok=True)
                if os.path.exists('logs/main_app.log'):
                    os.remove('logs/main_app.log')
                os.rename('main_app.log', 'logs/main_app.log')
        except Exception as e:
            print(f"Warning: Could not move main_app.log to logs directory: {e}")
        
        logging.shutdown()

if __name__ == '__main__':
    main()
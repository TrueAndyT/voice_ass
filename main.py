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
from services.llm_streaming_client import StreamingTTSIntegration
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
            sound_file = os.path.join(os.path.dirname(__file__), "sounds", "kwd_success.wav")
            
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
        log.info("Recording audio for transcription...")
    
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


def handle_wake_word_interaction(stt_service, llm_service, tts_service, log):
    """Handle the interaction after wake word detection."""
    try:
        log.info("Starting transcription after wake word detection")
        
        with audio_stream_manager(
            pyaudio.paInt16, 1, 16000, int(16000 * 0.03)
        ) as stream:
            audio_data = record_audio_for_transcription(stream, timeout_ms=3000, log=log)
        
        if not audio_data:
            log.warning("No audio data recorded")
            return
            
        transcription = stt_service.transcribe_audio_bytes(audio_data)
        
        if not transcription:
            log.warning("STT service returned no transcription")
            return
        
        speech_end_time = time.time()
        log.info(f"Transcription received: {transcription}")
        
        tts_start_time = time.time()
        log.info(f"LLM Query: {transcription}")
        
        try:
            # ✅ Replaced bridge with StreamingTTSIntegration
            integration = StreamingTTSIntegration(llm_service, tts_service, min_chunk_size=80)
            integration.speak_streaming_response(transcription)
            log.info("Streaming LLM to TTS completed")
            
        except Exception as e:
            log.warning(f"Streaming failed, falling back: {e}")
            llm_result = llm_service.get_response(transcription)
            llm_response = llm_result[0] if isinstance(llm_result, tuple) else llm_result
            tts_service.speak(llm_response)

        speech_to_tts_time = tts_start_time - speech_end_time
        log.info(f"Speech→TTS latency: {speech_to_tts_time:.2f}s")
        app_logger.log_performance("speech_to_tts", speech_to_tts_time)
        
        handle_followup_conversation(stt_service, llm_service, tts_service, log)
        log.info("Conversation ended - listening for wake word again")
        
    except Exception as e:
        log.error(f"Error during wake word interaction: {e}", exc_info=True)


def handle_followup_conversation(stt_service, llm_service, tts_service, log):
    """Handle the follow-up conversation loop."""
    while True:
        try:
            log.debug("Listening for follow-up...")
            
            with audio_stream_manager(
                pyaudio.paInt16, 1, 16000, int(16000 * 0.03)
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
            tts_start_time = time.time()
            
            try:
                # ✅ Replaced bridge with StreamingTTSIntegration
                integration = StreamingTTSIntegration(llm_service, tts_service, min_chunk_size=80)
                integration.speak_streaming_response(follow_up)
                log.info("Streaming follow-up LLM to TTS completed")
                
            except Exception as e:
                log.debug(f"Follow-up streaming failed, fallback: {e}")
                llm_result = llm_service.get_response(follow_up)
                llm_response = llm_result[0] if isinstance(llm_result, tuple) else llm_result
                tts_service.speak(llm_response)
            
            app_logger.log_performance("followup_speech_to_tts", tts_start_time - speech_end_time)
            
        except Exception as e:
            log.error(f"Error during follow-up conversation: {e}", exc_info=True)
            break


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
            # Enable KWD after successful initialization
            kwd_service.enable()
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
                    
                    # Process audio with wake word detection
                    prediction, utterance_buffer = kwd_service.process_audio(audio_chunk)
                    
                    # Handle wake word detection
                    if prediction:
                        log.info(f"Wake word detected! Confidence: {prediction}")
                        # Don't update intent here - let the wake word interaction handle it
                        handle_wake_word_interaction(stt_service, llm_service, tts_service, log)
                            
                except AudioException as e:
                    log.error(f"Audio processing error: {e}")
                    # if publisher:
                    #     publisher.publish({"state": "Audio Error"})
                    if not e.recoverable:
                        raise
                    # Continue for recoverable audio errors
                    time.sleep(0.1)
                    
                except Exception as e:
                    log.error(f"Unexpected error in main loop: {e}", exc_info=True)
                    # if publisher:
                    #     publisher.publish({"state": "Error"})
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
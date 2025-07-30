# Suppress common warnings at the very beginning
import warnings
import os
warnings.filterwarnings("ignore", message="pkg_resources is deprecated")

# Note: ALSA/JACK error suppression was removed due to segmentation faults
# The warnings will be visible but the application will be stable

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
from services.exceptions import (
    MicrophoneException, 
    ServiceInitializationException, 
    AudioException,
    VoiceAssistantException
)

def play_beep(sound_type="ready", log=None):
    """Play a short, pleasant system sound to indicate system readiness."""
    def _beep():
        try:
            # Use local project WAV files
            base_path = os.path.join(os.path.dirname(__file__), "config", "sounds")
            if sound_type == "ready":
                sound_file = os.path.join(base_path, "ready.wav")
            else:  # sound_type == "end"
                sound_file = os.path.join(base_path, "end.wav")
            
            # Check if file exists
            if not os.path.exists(sound_file):
                if log:
                    log.debug(f"Sound file not found: {sound_file}")
                raise FileNotFoundError(f"Sound file not found: {sound_file}")
            
            # Try multiple audio methods
            audio_methods = [
                f"paplay {sound_file}",
                f"aplay -q {sound_file}"
            ]
            
            for method in audio_methods:
                try:
                    result = subprocess.run(method, shell=True, timeout=2, 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        if log:
                            log.debug(f"Successfully played sound with: {method}")
                        return
                except subprocess.TimeoutExpired:
                    if log:
                        log.debug(f"Audio method timed out: {method}")
                except Exception as e:
                    if log:
                        log.debug(f"Audio method failed {method}: {e}")
            
            # If all audio methods failed
            if log:
                log.debug("All audio methods failed, falling back to system beep")
            raise Exception("All audio methods failed")
            
        except Exception as e:
            if log:
                log.debug(f"Could not play system sound: {e}")
            # Fallback to system beep methods
            beep_methods = [
                "printf '\a'",
                "echo -e '\a'"
            ]
            
            for method in beep_methods:
                try:
                    subprocess.run(method, shell=True, timeout=1)
                    if log:
                        log.debug(f"System beep with: {method}")
                    break
                except Exception as e2:
                    if log:
                        log.debug(f"Beep method failed {method}: {e2}")
                    continue
    
    # Run beep in a separate thread to avoid blocking
    threading.Thread(target=_beep, daemon=True).start()

@contextmanager
def audio_stream_manager(format_type, channels, rate, frames_per_buffer):
    """Context manager for PyAudio stream with proper cleanup."""
    pa = None
    stream = None
    try:
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


def handle_wake_word_interaction(stt_service, llm_service, tts_service, log):
    """Handle the interaction after wake word detection."""
    try:
        log.info("Starting transcription after wake word detection")
        
        # Record audio for transcription
        with audio_stream_manager(
            pyaudio.paInt16, 1, 16000, int(16000 * 0.03)  # 30ms frames
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
        
        # Process with LLM
        llm_start_time = time.time()
        llm_response = llm_service.get_response(transcription)
        llm_end_time = time.time()
        
        # Log performance metrics
        app_logger.log_performance(
            "llm_response", 
            llm_end_time - llm_start_time,
            {"input_length": len(transcription), "output_length": len(llm_response)}
        )
        
        # Speak response
        tts_start_time = time.time()
        log.info(f"LLM Response: {llm_response}")
        tts_service.speak(llm_response)
        
        app_logger.log_performance(
            "speech_to_tts", 
            tts_start_time - speech_end_time
        )
        
        # Handle follow-up conversation
        handle_followup_conversation(stt_service, llm_service, tts_service, log)
        
        # Play beep to indicate ready for next wake word
        log.info("Conversation ended - listening for wake word again")
        play_beep(sound_type="end", log=log)
        
    except Exception as e:
        log.error(f"Error during wake word interaction: {e}", exc_info=True)
        # Continue running - don't crash the main loop


def handle_followup_conversation(stt_service, llm_service, tts_service, log):
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
            llm_response = llm_service.get_response(follow_up)
            llm_end_time = time.time()
            
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
        log.info("Voice Assistant starting up...")
        
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
        log.info("Voice assistant ready - listening for wake word...")
        
        # Main application loop with audio stream management
        with audio_stream_manager(
            CONFIG["format"], 
            CONFIG["channels"], 
            CONFIG["rate"], 
            CONFIG["vad_frame_samples"]
        ) as stream:
            
            log.info("Main application loop started")
            
            # Play beep to indicate KWD is ready for wake word detection
            log.info("Wake word detection is now active - listening for 'Alexa'")
            play_beep(sound_type="ready", log=log)
            
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
                        handle_wake_word_interaction(stt_service, llm_service, tts_service, log)
                            
                except AudioException as e:
                    log.error(f"Audio processing error: {e}")
                    if not e.recoverable:
                        raise
                    # Continue for recoverable audio errors
                    time.sleep(0.1)
                    
                except Exception as e:
                    log.error(f"Unexpected error in main loop: {e}", exc_info=True)
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
        logging.shutdown()

if __name__ == '__main__':
    main()
# Suppress common warnings at the very beginning
import warnings
warnings.filterwarnings("ignore", message="pkg_resources is deprecated")

import pyaudio
import sys
import logging
from datetime import datetime
import time
import subprocess
from contextlib import contextmanager

# Import from the services package
from services.loader import load_services
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

@contextmanager
def audio_stream_manager(format_type, channels, rate, frames_per_buffer):
    """Context manager for PyAudio stream with proper cleanup."""
    pa = pyaudio.PyAudio()
    stream = None
    try:
        stream = pa.open(
            format=format_type, 
            channels=channels, 
            rate=rate, 
            input=True, 
            frames_per_buffer=frames_per_buffer
        )
        yield stream
    except OSError as e:
        raise MicrophoneException(
            "Could not open microphone stream",
            context={"error": str(e), "format": format_type, "rate": rate}
        )
    finally:
        if stream and stream.is_active():
            stream.stop_stream()
            stream.close()
        pa.terminate()


def handle_wake_word_interaction(stt_service, llm_service, tts_service, log):
    """Handle the interaction after wake word detection."""
    try:
        log.info("Starting transcription after wake word detection")
        transcription = stt_service.listen_and_transcribe(timeout_ms=3000)
        
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
        
    except Exception as e:
        log.error(f"Error during wake word interaction: {e}", exc_info=True)
        # Continue running - don't crash the main loop


def handle_followup_conversation(stt_service, llm_service, tts_service, log):
    """Handle the follow-up conversation loop."""
    while True:
        try:
            log.debug("Listening for follow-up...")
            follow_up = stt_service.listen_and_transcribe(timeout_ms=4000)
            
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


def main():
    """Main application entry point with enhanced error handling."""
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
        
        # Start memory logging
        mem_logger = MemoryLogger()
        mem_logger.start()
        
        # Load services with detailed error handling
        log.info("Loading services...")
        try:
            vad, oww_model, stt_service, llm_service, tts_service, dynamic_rms = load_services()
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
        
        # Main application loop with audio stream management
        with audio_stream_manager(
            CONFIG["format"], 
            CONFIG["channels"], 
            CONFIG["rate"], 
            CONFIG["vad_frame_samples"]
        ) as stream:
            
            log.info("Main application loop started")
            
            while True:
                try:
                    audio_chunk = stream.read(
                        CONFIG["vad_frame_samples"], 
                        exception_on_overflow=False
                    )
                    prediction, utterance_buffer = kwd_service.process_audio(audio_chunk)
                    
                    if prediction:
                        top_wakeword = max(prediction, key=prediction.get)
                        top_score = prediction[top_wakeword]
                        
                        if top_score >= CONFIG["wakeword_threshold"]:
                            log.info(
                                f"Wake word detected: {top_wakeword} (Score: {top_score:.2f})"
                            )
                            
                            # Play notification sound
                            try:
                                subprocess.run([
                                    "paplay", "--volume=16384",
                                    "/usr/share/sounds/freedesktop/stereo/complete.oga"
                                ], stderr=subprocess.DEVNULL, timeout=2)
                            except (subprocess.TimeoutExpired, FileNotFoundError) as e:
                                log.debug(f"Wake word beep failed: {e}")
                            
                            # Pause listening and handle interaction
                            stream.stop_stream()
                            
                            handle_wake_word_interaction(
                                stt_service, llm_service, tts_service, log
                            )
                            
                            # Resume listening
                            stream.start_stream()
                            kwd_service.enter_cooldown()
                            log.info("Waiting for wake word...")
                            
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
        log.info("Voice Assistant shutting down...")
        logging.shutdown()

if __name__ == '__main__':
    main()
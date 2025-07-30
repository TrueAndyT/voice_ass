import torch
import webrtcvad
import numpy as np
import os
import time
from openwakeword.model import Model
from .stt_service import STTService
from .llm_service import LLMService
from .tts_service import TTSService
from .dynamic_rms_service import DynamicRMSService
from .logger import app_logger
from .exceptions import ServiceInitializationException, ResourceException

def load_services():
    """Load all voice assistant services with comprehensive error handling."""
    log = app_logger.get_logger("loader")
    services = {}
    
    try:
        # Initialize VAD
        log.info("Initializing Voice Activity Detection...")
        vad = webrtcvad.Vad(1)
        services["vad"] = vad
        
        # Load wake word model
        log.info("Loading wake word detection model...")
        model_paths = [os.path.join("models", "alexa_v0.1.onnx")]
        
        # Verify model files exist
        for model_path in model_paths:
            if not os.path.exists(model_path):
                raise ResourceException(
                    f"Wake word model not found: {model_path}",
                    context={"model_path": model_path}
                )
        
        oww_model = Model(wakeword_model_paths=model_paths)
        services["oww_model"] = oww_model
        
        # Initialize core services
        try:
            log.info("Initializing Speech-to-Text service...")
            stt_service = STTService()
            services["stt_service"] = stt_service
        except Exception as e:
            raise ServiceInitializationException("STT", str(e))
        
        try:
            log.info("Initializing Language Model service...")
            llm_service = LLMService(model='llama3.1:8b-instruct-q4_K_M')
            services["llm_service"] = llm_service
        except Exception as e:
            raise ServiceInitializationException("LLM", str(e))
        
        try:
            log.info("Initializing Text-to-Speech service...")
            tts_service = TTSService()
            services["tts_service"] = tts_service
        except Exception as e:
            raise ServiceInitializationException("TTS", str(e))
        
        try:
            log.info("Initializing Dynamic RMS service...")
            dynamic_rms = DynamicRMSService()
            dynamic_rms.start()
            services["dynamic_rms"] = dynamic_rms
        except Exception as e:
            raise ServiceInitializationException("DynamicRMS", str(e))
        
        # Warm up models for better performance
        log.info("Warming up models for optimal performance...")
        _warmup_models(oww_model, stt_service, tts_service, llm_service, log)
        
        log.info("All services loaded and warmed up successfully")
        
        return vad, oww_model, stt_service, llm_service, tts_service, dynamic_rms
        
    except (ServiceInitializationException, ResourceException) as e:
        # Cleanup any partially initialized services
        _cleanup_services(services)
        
        # Re-raise the specific exception
        raise e
    except Exception as e:
        # Cleanup any partially initialized services
        _cleanup_services(services)
        
        # Wrap unexpected errors in ServiceInitializationException
        raise ServiceInitializationException(
            "service_loader",
            f"An unexpected error occurred during service loading: {str(e)}",
            context={
                "loaded_services": list(services.keys()),
                "error_type": type(e).__name__
            }
        ) from e


def _warmup_models(oww_model, stt_service, tts_service, llm_service, log):
    """Warm up all models with detailed timing and error handling."""
    warmup_times = {}
    
    # Warm up OpenWakeWord
    try:
        log.debug("Warming up OpenWakeWord model...")
        start_time = time.time()
        oww_chunk_samples = 1280
        silent_oww_chunk = np.zeros(oww_chunk_samples, dtype=np.int16)
        oww_model.predict(silent_oww_chunk)
        warmup_times["oww"] = time.time() - start_time
        log.debug(f"OpenWakeWord warmup completed in {warmup_times['oww']:.2f}s")
    except Exception as e:
        log.warning(f"OpenWakeWord warmup failed: {e}")
    
    # Warm up Whisper STT
    try:
        log.debug(f"Warming up Whisper STT model (device: {stt_service.device})...")
        start_time = time.time()
        if stt_service.device == 'cuda':
            rate = 16000
            silent_whisper_chunk = np.zeros(rate, dtype=np.float32)
            stt_service.model.transcribe(silent_whisper_chunk, fp16=True)
        warmup_times["stt"] = time.time() - start_time
        log.debug(f"Whisper STT warmup completed in {warmup_times['stt']:.2f}s")
    except Exception as e:
        log.warning(f"Whisper STT warmup failed: {e}")
    
    # Warm up TTS
    try:
        log.debug("Warming up TTS service...")
        start_time = time.time()
        tts_service.warmup()
        warmup_times["tts"] = time.time() - start_time
        log.debug(f"TTS warmup completed in {warmup_times['tts']:.2f}s")
    except Exception as e:
        log.warning(f"TTS warmup failed: {e}")
    
    # Warm up LLM
    try:
        log.debug("Warming up Language Model...")
        start_time = time.time()
        llm_service.warmup_llm()
        warmup_times["llm"] = time.time() - start_time
        log.debug(f"LLM warmup completed in {warmup_times['llm']:.2f}s")
    except Exception as e:
        log.warning(f"LLM warmup failed: {e}")
    
    # Log performance metrics
    total_warmup_time = sum(warmup_times.values())
    app_logger.log_performance(
        "model_warmup",
        total_warmup_time,
        warmup_times
    )
    
    log.info(f"Model warmup completed in {total_warmup_time:.2f} seconds")


def _cleanup_services(services):
    """Clean up partially initialized services."""
    log = app_logger.get_logger("loader")
    
    for service_name, service in services.items():
        try:
            if service_name == "dynamic_rms" and hasattr(service, 'stop'):
                service.stop()
                log.debug(f"Cleaned up {service_name}")
        except Exception as e:
            log.warning(f"Error cleaning up {service_name}: {e}")

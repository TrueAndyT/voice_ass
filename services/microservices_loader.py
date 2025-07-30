import torch
import webrtcvad
import numpy as np
import os
import time
import requests
from openwakeword.model import Model
from .stt_client import STTClient
from .llm_client import LLMClient
from .tts_client import TTSClient
from .dynamic_rms_service import DynamicRMSService
from .service_manager import ServiceManager
from .logger import app_logger
from .exceptions import ServiceInitializationException, ResourceException

def load_services_microservices():
    """Load voice assistant services using microservices architecture."""
    log = app_logger.get_logger("microservices_loader")
    service_manager = ServiceManager()
    services = {}
    
    try:
        log.info("Starting microservices-based voice assistant...")
        
        # Initialize VAD (runs locally for low latency)
        log.info("Initializing Voice Activity Detection...")
        vad = webrtcvad.Vad(1)
        services["vad"] = vad
        
        # Load wake word model (runs locally for low latency)
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
        
        # Start all microservices
        microservices = [
            ("tts_service", "services.tts_service_server:app", 8001),
            ("stt_service", "services.stt_service_server:app", 8002),
            ("llm_service", "services.llm_service_server:app", 8003)
        ]
        
        for service_name, app_path, port in microservices:
            log.info(f"Starting {service_name} microservice...")
            process = service_manager.start_service(
                service_name,
                f"python3 -m uvicorn {app_path} --host 0.0.0.0 --port {port}",
                port=port
            )
            
            if not process:
                raise ServiceInitializationException(service_name, f"Failed to start {service_name} microservice")
        
        # Initialize Dynamic RMS service (runs locally)
        try:
            log.info("Initializing Dynamic RMS service...")
            dynamic_rms = DynamicRMSService()
            dynamic_rms.start()
            services["dynamic_rms"] = dynamic_rms
        except Exception as e:
            raise ServiceInitializationException("DynamicRMS", str(e))
        
        # Create clients for microservices and wait for them to be ready
        log.info("Initializing microservice clients...")
        
        # TTS Client
        tts_service = TTSClient(port=8001)
        for attempt in range(30):
            if tts_service.health_check():
                log.info("TTS microservice is ready")
                break
            time.sleep(1)
        else:
            raise ServiceInitializationException("TTS", "TTS microservice failed to become ready")
        services["tts_service"] = tts_service
        
        # STT Client
        stt_service = STTClient(port=8002, dynamic_rms=dynamic_rms)
        for attempt in range(30):
            if stt_service.health_check():
                log.info("STT microservice is ready")
                break
            time.sleep(1)
        else:
            raise ServiceInitializationException("STT", "STT microservice failed to become ready")
        services["stt_service"] = stt_service
        
        # LLM Client
        llm_service = LLMClient(port=8003)
        for attempt in range(30):
            if llm_service.health_check():
                log.info("LLM microservice is ready")
                break
            time.sleep(1)
        else:
            raise ServiceInitializationException("LLM", "LLM microservice failed to become ready")
        services["llm_service"] = llm_service
        
        # Warm up models
        log.info("Warming up models for optimal performance...")
        _warmup_models_microservices(oww_model, stt_service, tts_service, llm_service, log)
        
        log.info("All services loaded and warmed up successfully")
        
        return vad, oww_model, stt_service, llm_service, tts_service, dynamic_rms, service_manager
        
    except Exception as e:
        log.error(f"Failed to load microservices: {e}", exc_info=True)
        # Cleanup
        service_manager.stop_all_services()
        _cleanup_services(services)
        raise

def _warmup_models_microservices(oww_model, stt_service, tts_service, llm_service, log):
    """Warm up all models with detailed timing and error handling."""
    warmup_times = {}
    
    # Warm up OpenWakeWord (runs locally)
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
    
    # Warm up TTS microservice
    try:
        log.debug("Warming up TTS microservice...")
        start_time = time.time()
        tts_service.warmup()
        warmup_times["tts"] = time.time() - start_time
        log.debug(f"TTS microservice warmup completed in {warmup_times['tts']:.2f}s")
    except Exception as e:
        log.warning(f"TTS microservice warmup failed: {e}")
    
    # Warm up LLM microservice
    try:
        log.debug("Warming up LLM microservice...")
        start_time = time.time()
        llm_service.warmup_llm()
        warmup_times["llm"] = time.time() - start_time
        log.debug(f"LLM microservice warmup completed in {warmup_times['llm']:.2f}s")
    except Exception as e:
        log.warning(f"LLM microservice warmup failed: {e}")
    
    # Note: STT microservice warmup happens during service initialization
    # No additional warmup needed for STT client
    
    # Log performance metrics
    total_warmup_time = sum(warmup_times.values())
    app_logger.log_performance(
        "microservices_warmup",
        total_warmup_time,
        warmup_times
    )
    
    log.info(f"Model warmup completed in {total_warmup_time:.2f} seconds")

def _cleanup_services(services):
    """Clean up partially initialized services."""
    log = app_logger.get_logger("microservices_loader")
    
    for service_name, service in services.items():
        try:
            if service_name == "dynamic_rms" and hasattr(service, 'stop'):
                service.stop()
                log.debug(f"Cleaned up {service_name}")
        except Exception as e:
            log.warning(f"Error cleaning up {service_name}: {e}")

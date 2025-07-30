#!/usr/bin/env python3
"""
Test script to verify the microservices architecture works correctly.
"""

import time
import sys
from services.microservices_loader import load_services_microservices
from services.logger import app_logger

def test_microservices():
    """Test the microservices setup."""
    log = app_logger.get_logger("microservices_test")
    
    try:
        log.info("🧪 Testing microservices architecture...")
        
        # Load services using microservices architecture
        result = load_services_microservices()
        vad, oww_model, stt_service, llm_service, tts_service, dynamic_rms, service_manager = result
        
        log.info("✅ All services loaded successfully!")
        
        # Test TTS microservice
        log.info("Testing TTS microservice...")
        try:
            tts_service.speak("Hello, this is a test of the TTS microservice!")
            log.info("✅ TTS microservice test passed!")
        except Exception as e:
            log.error(f"❌ TTS microservice test failed: {e}")
        
        # Keep running for a few seconds to observe
        log.info("Keeping services running for 10 seconds...")
        time.sleep(10)
        
        # Cleanup
        log.info("Stopping all services...")
        service_manager.stop_all_services()
        log.info("✅ All services stopped successfully!")
        
    except Exception as e:
        log.error(f"❌ Microservices test failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    test_microservices()

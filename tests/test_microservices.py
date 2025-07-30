#!/usr/bin/env python3
"""
Test script to verify the microservices architecture works correctly.
"""

import time
import sys
import os

# Add parent directory to path so we can import services
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
        
        # Test STT microservice
        log.info("Testing STT microservice...")
        try:
            # Create a dummy audio file for testing
            import numpy as np
            dummy_audio = np.random.randint(-32768, 32767, 16000, dtype=np.int16)
            transcription = stt_service._send_for_transcription(dummy_audio.tobytes())
            log.info(f"✅ STT microservice transcription: {transcription}")
        except Exception as e:
            log.error(f"❌ STT microservice test failed: {e}")

        # Test LLM microservice
        log.info("Testing LLM microservice...")
        try:
            response = llm_service.get_response("Hello, who are you?")
            log.info(f"✅ LLM microservice response: {response}")
        except Exception as e:
            log.error(f"❌ LLM microservice test failed: {e}")
        
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

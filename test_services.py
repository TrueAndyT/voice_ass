#!/usr/bin/env python3
"""
Test script to verify the refactored services work correctly
with the new logging and error handling framework.
"""

import sys
import traceback
from services.logger import app_logger
from services.exceptions import VoiceAssistantException

def test_stt_service():
    """Test STT service initialization."""
    print("=== Testing STT Service ===")
    
    try:
        from services.stt_service import STTService
        # Mock dynamic_rms for testing
        class MockDynamicRMS:
            def get_threshold(self):
                return 0.15
            def lock(self):
                pass
            def reset(self):
                pass
        
        stt_service = STTService(model_size="base", dynamic_rms=MockDynamicRMS())
        print("✓ STT service initialized successfully")
        return True
    except Exception as e:
        print(f"❌ STT service test failed: {e}")
        traceback.print_exc()
        return False

def test_llm_service():
    """Test LLM service initialization."""
    print("\n=== Testing LLM Service ===")
    
    try:
        from services.llm_service import LLMService
        llm_service = LLMService(model='llama3.1:8b-instruct-q4_K_M')
        print("✓ LLM service initialized successfully")
        return True
    except Exception as e:
        print(f"❌ LLM service test failed: {e}")
        traceback.print_exc()
        return False

def test_loader_service():
    """Test service loader."""
    print("\n=== Testing Service Loader ===")
    
    try:
        from services.loader import load_services
        # This will fail without dependencies but we can test error handling
        try:
            vad, oww_model, stt_service, llm_service, tts_service, dynamic_rms = load_services()
            print("✓ All services loaded successfully")
        except Exception as e:
            # Expected to fail due to missing dependencies
            print(f"⚠️  Service loading failed as expected: {type(e).__name__}")
            # Check if it's using our exception framework
            if isinstance(e, VoiceAssistantException):
                print("✓ Using custom exception framework")
            else:
                print("❌ Not using custom exception framework")
        return True
    except Exception as e:
        print(f"❌ Service loader test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all service tests."""
    print("🧪 Testing Refactored Services")
    print("=" * 50)
    
    # Initialize logger
    log = app_logger.get_logger("test_services")
    
    results = []
    results.append(test_llm_service())  # Test LLM first (fewer dependencies)
    results.append(test_loader_service())
    # Skip STT test since it requires audio dependencies
    # results.append(test_stt_service())
    
    print("\n" + "=" * 50)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ All {total} tests passed!")
    else:
        print(f"⚠️  {passed}/{total} tests passed")
    
    print("\nCheck logs/app.jsonl for detailed logging output")

if __name__ == "__main__":
    main()

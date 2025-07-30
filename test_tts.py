#!/usr/bin/env python3
"""Test script to verify TTS functionality"""

import sys
import time

# Add project root to path
sys.path.insert(0, '/home/master/Projects/test')

from services.tts_client import TTSClient

def test_tts():
    print("Testing TTS functionality...")
    
    try:
        # Initialize TTS client
        print("Initializing TTS client...")
        tts_client = TTSClient(port=8001)
        
        # Check if service is healthy
        print("Checking TTS service health...")
        if tts_client.health_check():
            print("✓ TTS service is healthy")
        else:
            print("✗ TTS service is not responding")
            return
        
        # Test speaking
        test_message = "Hello! This is a test of the text to speech system."
        print(f"Testing speech with message: '{test_message}'")
        
        try:
            tts_client.speak(test_message)
            print("✓ TTS speak command sent successfully")
            time.sleep(3)  # Wait for speech to complete
        except Exception as e:
            print(f"✗ TTS speak failed: {e}")
            
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_tts()

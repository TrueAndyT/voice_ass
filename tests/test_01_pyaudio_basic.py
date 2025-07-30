#!/usr/bin/env python3
"""
Test 1: Basic PyAudio Functionality 
Verifies that PyAudio can be imported, instantiated, and create audio streams.
"""

import pyaudio
import time
import numpy as np

def test_pyaudio_basic():
    print("=== Test 1: Basic PyAudio Functionality ===")
    
    try:
        print("1. Importing PyAudio... ✓")
        
        print("2. Creating PyAudio instance...")
        pa = pyaudio.PyAudio()
        print("   PyAudio instance created ✓")
        
        print("3. Listing audio devices...")
        device_count = pa.get_device_count()
        print(f"   Found {device_count} audio devices")
        
        # Find default input device
        default_input = pa.get_default_input_device_info()
        print(f"   Default input device: {default_input['name']}")
        
        print("4. Opening audio stream...")
        stream = pa.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=480
        )
        print("   Audio stream opened ✓")
        
        print("5. Reading audio data...")
        for i in range(5):
            data = stream.read(480, exception_on_overflow=False)
            audio_np = np.frombuffer(data, dtype=np.int16)
            rms = np.sqrt(np.mean(audio_np.astype(np.float32)**2))
            print(f"   Sample {i+1}: RMS = {rms:.4f}")
            time.sleep(0.1)
        
        print("6. Closing stream...")
        stream.stop_stream()
        stream.close()
        print("   Stream closed ✓")
        
        print("7. Terminating PyAudio...")
        pa.terminate()
        print("   PyAudio terminated ✓")
        
        print("\n🎉 Test 1 PASSED: Basic PyAudio functionality works!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test 1 FAILED: {e}")
        return False

if __name__ == "__main__":
    test_pyaudio_basic()

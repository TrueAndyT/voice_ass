#!/usr/bin/env python3
"""
Test 2: Wake Word Detection Service
Verifies that the KWDService can process audio data without crashing.
"""

import numpy as np
import time
from openwakeword.model import Model
from services.kwd_service import KWDService
from services.dynamic_rms_service import DynamicRMSService
import webrtcvad

def test_kwd_service():
    print("\n=== Test 2: Wake Word Detection Service ===")
    
    try:
        print("1. Initializing VAD...")
        vad = webrtcvad.Vad(1)
        print("   VAD initialized ✓")
        
        print("2. Loading wake word model...")
        oww_model = Model(wakeword_model_paths=["models/alexa_v0.1.onnx"])
        print("   Wake word model loaded ✓")
        
        print("3. Initializing DynamicRMSService...")
        dynamic_rms = DynamicRMSService()
        print("   DynamicRMSService initialized ✓")
        
        print("4. Initializing KWDService...")
        kwd_service = KWDService(oww_model, vad, dynamic_rms)
        print("   KWDService initialized ✓")
        
        print("5. Processing silent audio chunks...")
        # Create silent audio data (30ms frames at 16kHz = 480 samples)
        chunk_samples = 480  # 16000 * 0.03 = 480 samples for 30ms frames
        silent_chunk = np.zeros(chunk_samples, dtype=np.int16)
        silent_audio_data = silent_chunk.tobytes()
        
        for i in range(5):
            prediction, _ = kwd_service.process_audio(silent_audio_data)
            if prediction:
                print(f"   Sample {i+1}: Prediction found (unexpected but not a failure)")
            else:
                print(f"   Sample {i+1}: No prediction ✓")
            time.sleep(0.1)
            
        print("5. Processing simulated speech audio...")
        # Create some noisy audio to simulate speech
        noisy_chunk = (np.random.rand(chunk_samples) * 32767).astype(np.int16)
        noisy_audio_data = noisy_chunk.tobytes()
        
        prediction, _ = kwd_service.process_audio(noisy_audio_data)
        if prediction:
            print("   Simulated speech processed ✓")
        else:
            print("   Simulated speech processed (no prediction) ✓")

        print("\n🎉 Test 2 PASSED: KWDService processes audio successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test 2 FAILED: {e}")
        return False

if __name__ == "__main__":
    test_kwd_service()


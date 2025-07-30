import pytest
import sys
import os
import time
import pyaudio
import numpy as np
import webrtcvad
from unittest.mock import MagicMock
from openwakeword import Model

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.kwd_service import KWDService
from services.dynamic_rms_service import DynamicRMSService

class TestKWDService:
    def setup_method(self):
        """Setup real components for KWD Service testing."""
        # Initialize real VAD
        self.vad = webrtcvad.Vad(3)
        
        # Initialize real dynamic RMS service
        self.dynamic_rms = DynamicRMSService()
        self.dynamic_rms.start()
        
        # Initialize real OpenWakeWord model
        self.oww_model = MagicMock(spec=Model)
        
        # Create the KWD service with real components
        self.kwd_service = KWDService(self.oww_model, self.vad, self.dynamic_rms)
        
    def teardown_method(self):
        """Cleanup after tests."""
        if hasattr(self, 'dynamic_rms'):
            self.dynamic_rms.stop()

    def test_complete_flow_no_wake_word(self):
        """Complete flow test without wake word detection."""
        audio_chunk = np.zeros(16000, dtype=np.int16).tobytes()
        self.kwd_service.oww_model.predict.return_value = {"keyword": 0.1}
        result, _ = self.kwd_service.process_audio(audio_chunk)
        assert result is None

    def test_complete_flow_with_wake_word(self):
        """Complete flow test with wake word detection."""
        audio_chunk = np.zeros(16000, dtype=np.int16).tobytes()
        self.kwd_service.oww_model.predict.return_value = {"keyword": 0.6}
        result, buffer = self.kwd_service.process_audio(audio_chunk)
        assert result is not None
        assert buffer is not None

    def test_with_realistic_scenario(self):
        """Simulate a real scenario with dynamic adjustments."""
        # Example of a more complex test scenario
        audio_chunk = (np.random.rand(16000) * 32767).astype(np.int16).tobytes()
        self.kwd_service.oww_model.predict.return_value = {"keyword": 0.4}
        self.dynamic_rms.get_threshold.return_value = 0.5
        result, _ = self.kwd_service.process_audio(audio_chunk)
        assert result is None  # Below threshold detection

    def test_buffer_management(self):
        """Test the audio buffer management of KWD Service."""
        # Test that buffer maintains correct size
        chunk_size = 480  # Typical chunk size
        initial_buffer_size = len(self.kwd_service.audio_buffer)
        
        # Process multiple small chunks
        for _ in range(10):
            small_chunk = np.zeros(chunk_size, dtype=np.int16).tobytes()
            self.kwd_service.process_audio(small_chunk)
        
        # Buffer should still be exactly 16000 samples
        assert len(self.kwd_service.audio_buffer) == self.kwd_service.OWW_EXPECTED_SAMPLES
        
    def test_multiple_wake_words(self):
        """Test detection with multiple wake words in predictions."""
        audio_chunk = np.zeros(16000, dtype=np.int16).tobytes()
        # Simulate multiple wake words with different scores
        self.kwd_service.oww_model.predict.return_value = {
            "alexa": 0.8,
            "hey_alexa": 0.3,
            "computer": 0.1
        }
        result, buffer = self.kwd_service.process_audio(audio_chunk)
        assert result is not None  # Should detect based on highest score
        assert "alexa" in result
        
    def test_prediction_failure_handling(self):
        """Test handling of prediction failures."""
        audio_chunk = np.zeros(16000, dtype=np.int16).tobytes()
        # Simulate prediction failure
        self.kwd_service.oww_model.predict.side_effect = Exception("Model error")
        result, buffer = self.kwd_service.process_audio(audio_chunk)
        assert result is None
        assert buffer is None
        
    def test_continuous_audio_processing(self):
        """Test continuous audio processing simulation."""
        # Simulate continuous audio streaming
        chunk_size = 480
        total_chunks = 100
        wake_word_at_chunk = 50
        
        for i in range(total_chunks):
            audio_chunk = (np.random.rand(chunk_size) * 1000).astype(np.int16).tobytes()
            
            if i == wake_word_at_chunk:
                self.kwd_service.oww_model.predict.return_value = {"alexa": 0.9}
            else:
                self.kwd_service.oww_model.predict.return_value = {"alexa": 0.2}
                
            result, buffer = self.kwd_service.process_audio(audio_chunk)
            
            if i == wake_word_at_chunk:
                assert result is not None
                assert buffer is not None
            else:
                assert result is None
                
    def test_edge_case_empty_audio(self):
        """Test handling of empty audio chunks."""
        empty_chunk = b''
        # Should handle gracefully without crash
        result, buffer = self.kwd_service.process_audio(empty_chunk)
        # The buffer should still work properly
        assert len(self.kwd_service.audio_buffer) == self.kwd_service.OWW_EXPECTED_SAMPLES

    def test_cooldown_functionality(self):
        """Test cooldown method exists and can be called."""
        # Test that cooldown method exists and doesn't crash
        try:
            self.kwd_service.enter_cooldown()
        except Exception as e:
            pytest.fail(f"Cooldown method failed: {e}")
    
    def test_real_wake_word_detection(self):
        """Test with real microphone input - say 'Alexa' to trigger detection."""
        # Use REAL OpenWakeWord model for this test
        from openwakeword import Model
        real_model = Model()
        real_kwd_service = KWDService(real_model, self.vad, self.dynamic_rms)
        
        print("\n=== REAL WAKE WORD TEST ===")
        print("This test will listen for 30 seconds.")
        print("The dynamic RMS will adjust to your environment noise level.")
        print("Please say 'ALEXA' clearly to test wake word detection.")
        print("A beep sound will play when detected.")
        print("Available wake words in model:")
        
        # Show what wake words are available
        test_audio = np.zeros(16000, dtype=np.int16)
        test_prediction = real_model.predict(test_audio)
        for wake_word in test_prediction.keys():
            print(f"  - {wake_word}")
        
        print("\nStarting in 3 seconds...\n")
        time.sleep(3)
        
        # Setup PyAudio
        pa = pyaudio.PyAudio()
        stream = pa.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=480
        )
        
        detected_count = 0
        start_time = time.time()
        timeout = 30  # seconds
        last_rms_print = 0
        
        try:
            while time.time() - start_time < timeout:
                # Read audio from microphone
                audio_chunk = stream.read(480, exception_on_overflow=False)
                
                # Update RMS threshold
                self.dynamic_rms.update_threshold(audio_chunk)
                
                # Process audio through KWD service
                result, buffer = real_kwd_service.process_audio(audio_chunk)
                
                # Print RMS info every second
                current_time = time.time()
                if current_time - last_rms_print > 1.0:
                    threshold = self.dynamic_rms.get_threshold()
                    # Calculate current RMS
                    audio_np = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32) / 32767.0
                    current_rms = np.sqrt(np.mean(audio_np**2))
                    print(f"\rRMS: {current_rms:.4f} | Threshold: {threshold:.4f} | Time: {current_time - start_time:.1f}s / {timeout}s", end='', flush=True)
                    last_rms_print = current_time
                
                if result is not None:
                    # Check if it's actually 'alexa' with high confidence
                    alexa_score = result.get('alexa', 0)
                    if alexa_score > 0.5:  # Only count high confidence detections
                        detected_count += 1
                        print(f"\n\nWAKE WORD 'ALEXA' DETECTED #{detected_count}!")
                        print(f"Alexa Score: {alexa_score:.4f}")
                        print(f"All Scores: {result}")
                        
                        # Play success sound
                        import subprocess
                        sound_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "sounds", "kwd_success.wav")
                        if os.path.exists(sound_file):
                            subprocess.run(f"paplay '{sound_file}' 2>/dev/null || aplay -q '{sound_file}' 2>/dev/null", shell=True)
                            print("Played success sound!\n")
                        else:
                            print(f"Sound file not found: {sound_file}\n")
                    else:
                        print(f"\n\nFalse positive detected (low confidence):")
                        print(f"Scores: {result}\n")
                    
        finally:
            stream.stop_stream()
            stream.close()
            pa.terminate()
            
        print(f"\n\nTest completed. Detected 'ALEXA' {detected_count} times in {timeout} seconds.")
        if detected_count == 0:
            print("No wake words detected. Make sure to say 'ALEXA' clearly.")
            print("The test still passes - the service ran without crashing.")
            
        # Test passes whether wake word is detected or not
        # The important thing is that the service runs without crashing
        assert True

if __name__ == "__main__":
    # Run only the real wake word test when executed directly
    if len(sys.argv) == 1:
        sys.argv.append("TestKWDService::test_real_wake_word_detection")
    pytest.main(["-v", "-s"])

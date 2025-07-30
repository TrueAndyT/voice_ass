import numpy as np
import unittest
from unittest.mock import MagicMock, patch
from collections import deque

# Adjust the import path to match your project structure
from services.kwd_service import KWDService

class TestKWDSlidingWindow(unittest.TestCase):

    def setUp(self):
        """Set up a mock environment for each test."""
        self.oww_model = MagicMock()
        self.vad = MagicMock()  # VAD is not used in the new implementation
        self.dynamic_rms = MagicMock()  # Not used
        self.kwd_service = KWDService(self.oww_model, self.vad, self.dynamic_rms)

    @patch('logging.getLogger')
    def test_sliding_window_prediction(self, mock_logger):
        """Test that the service continuously predicts on a 1-second sliding window."""
        # Simulate a stream of audio chunks (e.g., 30ms each)
        chunk_size = 480  # 30ms at 16kHz
        num_chunks = 50  # Simulate 1.5 seconds of audio

        # Mock the prediction result
        self.oww_model.predict.return_value = {'alexa': 0.2}

        for i in range(num_chunks):
            audio_chunk = np.random.randint(-100, 100, size=chunk_size, dtype=np.int16).tobytes()
            self.kwd_service.process_audio(audio_chunk)
        
        # Verification
        # The predict method should have been called for each chunk processed
        self.assertEqual(self.oww_model.predict.call_count, num_chunks)

        # Check the type and shape of the data sent to predict
        last_call_args = self.oww_model.predict.call_args[0][0]
        self.assertIsInstance(last_call_args, np.ndarray)
        self.assertEqual(last_call_args.shape, (self.kwd_service.OWW_EXPECTED_SAMPLES,))

    @patch('logging.getLogger')
    def test_wake_word_detection(self, mock_logger):
        """Test that a wake word detection returns the prediction and buffer."""
        chunk_size = 480
        
        # No detection initially
        self.oww_model.predict.return_value = {'alexa': 0.2}
        no_detection_chunk = np.zeros(chunk_size, dtype=np.int16).tobytes()
        result = self.kwd_service.process_audio(no_detection_chunk)
        self.assertIsNone(result[0])
        self.assertIsNone(result[1])
        
        # Simulate a detection
        self.oww_model.predict.return_value = {'alexa': 0.8}
        detection_chunk = np.random.randint(1000, 2000, size=chunk_size, dtype=np.int16).tobytes()
        prediction, buffer = self.kwd_service.process_audio(detection_chunk)
        
        # Verification
        self.assertIsNotNone(prediction)
        self.assertEqual(prediction['alexa'], 0.8)
        self.assertIsInstance(buffer, np.ndarray)
        self.assertEqual(len(buffer), self.kwd_service.OWW_EXPECTED_SAMPLES)

if __name__ == '__main__':
    unittest.main()

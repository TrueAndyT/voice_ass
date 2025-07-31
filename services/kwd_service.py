import numpy as np
import logging
from collections import deque
import time

class KWDService:
    # --- Configuration ---
    RATE = 16000
    MAX_INT16 = 32767.0
    OWW_EXPECTED_SAMPLES = 16000  # openwakeword expects 1 second of audio
    COOLDOWN_SECONDS = 2.0  # Cooldown period after detection

    def __init__(self, oww_model, vad, dynamic_rms):
        self.log = logging.getLogger("KWD")
        self.oww_model = oww_model
        self.vad = vad
        self.dynamic_rms = dynamic_rms
        
        # Buffer to hold exactly 1 second of audio data for openwakeword
        self.audio_buffer = deque(maxlen=self.OWW_EXPECTED_SAMPLES)
        # Initialize with silence
        self.audio_buffer.extend(np.zeros(self.OWW_EXPECTED_SAMPLES, dtype=np.int16))
        
        # Cooldown tracking
        self.last_detection_time = 0
        self.in_cooldown = False
        
        # KWD control
        self.enabled = False  # KWD starts disabled

    def enable(self):
        """Enable wake word detection."""
        self.enabled = True
        self.log.info("Wake word detection enabled")
    
    def disable(self):
        """Disable wake word detection."""
        self.enabled = False
        self.log.info("Wake word detection disabled")
    
    def process_audio(self, audio_chunk_bytes):
        """
        Continuously processes audio chunks, feeding them into a sliding 
        1-second buffer for wake word detection.
        """
        # Skip processing if KWD is disabled
        if not self.enabled:
            return None, None
        
        # Convert raw bytes to numpy array
        chunk_np = np.frombuffer(audio_chunk_bytes, dtype=np.int16)
        
        # Add new audio to the right of the buffer, pushing out old audio from the left
        self.audio_buffer.extend(chunk_np)
        
        # Check if we're in cooldown period
        current_time = time.time()
        if self.in_cooldown:
            if current_time - self.last_detection_time < self.COOLDOWN_SECONDS:
                return None, None
            else:
                self.in_cooldown = False
                self.log.debug("Cooldown period ended")
        
        # === Audio filtering before wake word detection ===
        
        # 1. Check RMS threshold - skip if audio is too quiet (background noise)
        dynamic_threshold = self.dynamic_rms.get_threshold()
        audio_np = chunk_np.astype(np.float32) / self.MAX_INT16
        current_rms = np.sqrt(np.mean(audio_np**2))
        
        if current_rms <= dynamic_threshold:
            # Audio is below dynamic threshold, likely background noise
            return None, None
        
        # 2. Use VAD to confirm voice activity
        try:
            is_speech = self.vad.is_speech(audio_chunk_bytes, sample_rate=self.RATE)
            if not is_speech:
                # No voice activity detected
                return None, None
        except Exception as e:
            self.log.debug(f"VAD error: {e}, proceeding without VAD check")
        
        # === Proceed with wake word detection ===
        
        # Get the current 1-second window for prediction
        prediction_buffer = np.array(self.audio_buffer, dtype=np.int16)

        # Ensure the buffer is exactly the size OWW expects
        if len(prediction_buffer) != self.OWW_EXPECTED_SAMPLES:
            self.log.warning(
                f"Prediction buffer size is {len(prediction_buffer)}, expected "
                f"{self.OWW_EXPECTED_SAMPLES}. Skipping prediction."
            )
            return None, None

        try:
            # Send the 1-second buffer to the wake word model
            prediction = self.oww_model.predict(prediction_buffer)
            
            # Check if any score is above the required threshold of 0.77
            if any(score > 0.77 for score in prediction.values()):
                self.log.info(f"Wake word detected! Scores: {prediction}")
                # Enter cooldown period
                self.enter_cooldown()
                # Return the full buffer that contains the wake word
                return prediction, prediction_buffer

        except Exception as e:
            self.log.error(f"Wake word prediction failed: {e}")
        
        return None, None

    def enter_cooldown(self):
        """Enter cooldown period to prevent multiple detections from one utterance."""
        self.in_cooldown = True
        self.last_detection_time = time.time()
        self.log.debug(f"Entering cooldown for {self.COOLDOWN_SECONDS} seconds")

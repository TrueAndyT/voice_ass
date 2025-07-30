import numpy as np
import threading
import time
import pyaudio
import webrtcvad

class DynamicRMSService:
    def __init__(self, sample_rate=16000, frame_ms=30, window_seconds=3, multiplier=2.0):
        self.sample_rate = sample_rate
        self.frame_samples = int(sample_rate * frame_ms / 1000)
        self.vad = webrtcvad.Vad(3)
        self.multiplier = multiplier
        self.locked = False
        self.rms_values = []
        self.window_size = int(window_seconds * 1000 / frame_ms)
        self.threshold = 0.15  # fallback default
        self.running = False
        self._lock = threading.Lock()

    def start(self):
        if self.running:
            return
        self.running = True
        # Background thread disabled to prevent PyAudio conflicts
        # The main application will call update_threshold() directly

    def stop(self):
        self.running = False

    def lock(self):
        with self._lock:
            self.locked = True

    def reset(self):
        with self._lock:
            self.locked = False
            self.rms_values.clear()

    def get_threshold(self):
        with self._lock:
            return self.threshold
    
    def update_threshold(self, audio_chunk):
        """Manually update threshold based on audio chunk from main application."""
        try:
            audio_np = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32) / 32767.0
            rms = np.sqrt(np.mean(audio_np**2))
            
            try:
                is_speech = self.vad.is_speech(audio_chunk, sample_rate=self.sample_rate)
            except Exception as e:
                print(f"[ERROR] VAD failure in RMS update: {e}")
                is_speech = False  # fallback
            
            with self._lock:
                if not self.locked and not is_speech:
                    self.rms_values.append(rms)
                    if len(self.rms_values) > self.window_size:
                        self.rms_values.pop(0)
                    if self.rms_values:
                        self.threshold = np.mean(self.rms_values) * self.multiplier
        except Exception as e:
            print(f"[ERROR] Failed to update RMS threshold: {e}")

    def _monitor_loop(self):
        # Disabled independent audio monitoring to prevent PyAudio conflicts
        # The main application will handle audio processing and call update_threshold() directly
        while self.running:
            time.sleep(0.1)  # Keep thread alive but don't do audio processing

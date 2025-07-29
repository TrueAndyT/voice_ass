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
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()

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

    def _monitor_loop(self):
        pa = pyaudio.PyAudio()
        stream = pa.open(format=pyaudio.paInt16, channels=1, rate=self.sample_rate, input=True,
                         frames_per_buffer=self.frame_samples)

        while self.running:
            chunk = stream.read(self.frame_samples, exception_on_overflow=False)
            audio_np = np.frombuffer(chunk, dtype=np.int16).astype(np.float32) / 32767.0
            rms = np.sqrt(np.mean(audio_np**2))

            try:
                is_speech = self.vad.is_speech(chunk, sample_rate=self.sample_rate)
            except Exception as e:
                print(f"[ERROR] VAD failure in RMS thread: {e}")
                is_speech = False  # fallback

            with self._lock:
                if not self.locked and not is_speech:
                    self.rms_values.append(rms)
                    if len(self.rms_values) > self.window_size:
                        self.rms_values.pop(0)
                    if self.rms_values:
                        self.threshold = np.mean(self.rms_values) * self.multiplier

            print(f"[DYN RMS] rms={rms:.3f} | speech={is_speech} | locked={self.locked} | threshold={self.threshold:.3f}", end='\r')
            time.sleep(0.1)


        stream.stop_stream()
        stream.close()
        pa.terminate()

import torch
from kokoro import KPipeline
import sounddevice as sd
import numpy as np
import threading
import time

class TTSService:
    """Kokoro TTS with interrupt support."""
    def __init__(self, voice_model='af_heart'):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Kokoro TTS using device: {self.device}")
        self.pipeline = KPipeline(lang_code='a', device=self.device)
        self.voice_model = voice_model
        self.sample_rate = 24000
        self._interrupted = threading.Event()

    def speak(self, text):
        print(f"TTS saying: '{text}'")
        self._interrupted.clear()
        try:
            generator = self.pipeline(text, voice=self.voice_model)
            all_audio_chunks = []

            for _, _, audio in generator:
                if self._interrupted.is_set():
                    print("🔇 TTS interrupted during generation.")
                    return
                if isinstance(audio, torch.Tensor):
                    audio = audio.cpu().numpy()
                if audio.dtype != np.float32:
                    audio = audio.astype(np.float32) / np.iinfo(audio.dtype).max
                all_audio_chunks.append(audio)

            if all_audio_chunks:
                full_audio = np.concatenate(all_audio_chunks)
                stream = sd.OutputStream(samplerate=self.sample_rate, channels=1, dtype='float32')
                with stream:
                    stream.start()
                    i = 0
                    block_size = 1024
                    while i < len(full_audio) and not self._interrupted.is_set():
                        end = min(i + block_size, len(full_audio))
                        stream.write(full_audio[i:end])
                        i = end
                    if self._interrupted.is_set():
                        print("🔇 TTS playback interrupted.")
                        stream.abort()

        except Exception as e:
            print(f"Error during TTS playback: {e}")

    def warmup(self):
        print("Warming up Kokoro TTS...")
        try:
            generator = self.pipeline(" ", voice=self.voice_model)
            for _ in generator:
                pass
            print("Kokoro TTS is ready.")
        except Exception as e:
            print(f"Error during TTS warmup: {e}")

    def interrupt(self):
        """Interrupts current playback."""
        self._interrupted.set()

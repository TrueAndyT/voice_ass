import torch
from kokoro import KPipeline
import sounddevice as sd
import numpy as np

class TTSService:
    """A service for text-to-speech using the Kokoro TTS model."""

    def __init__(self, voice_model='af_heart'):
        if torch.cuda.is_available():
            self.device = "cuda"
        else:
            self.device = "cpu"
        
        print(f"Kokoro TTS using device: {self.device}")
        
        self.pipeline = KPipeline(lang_code='a', device=self.device)
        self.voice_model = voice_model
        self.sample_rate = 24000

    def speak(self, text):
        """
        Generates audio from text and plays it.
        This version concatenates all audio chunks before playback for stability.
        """
        print(f"TTS saying: '{text}'")
        try:
            generator = self.pipeline(text, voice=self.voice_model)
            
            all_audio_chunks = []
            for i, (gs, ps, audio) in enumerate(generator):
                if isinstance(audio, torch.Tensor):
                    audio = audio.cpu().numpy()
                
                if audio.dtype != np.float32:
                     audio = audio.astype(np.float32) / np.iinfo(audio.dtype).max
                
                all_audio_chunks.append(audio)

            # Check if any audio was generated
            if all_audio_chunks:
                # Combine all chunks into a single audio array
                full_audio = np.concatenate(all_audio_chunks)
                
                # Play the consolidated audio and wait for it to finish
                sd.play(full_audio, self.sample_rate)
                sd.wait()
            
        except Exception as e:
            print(f"Error during TTS playback: {e}")

    def warmup(self):
        """Warms up the TTS model."""
        print("Warming up Kokoro TTS...")
        try:
            generator = self.pipeline(" ", voice=self.voice_model)
            for _ in generator:
                pass
            print("Kokoro TTS is ready.")
        except Exception as e:
            print(f"Error during TTS warmup: {e}")
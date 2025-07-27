import pyaudio
import numpy as np
from kokoro.tts import TTS # Using the correct 'kokoro' library

class TTSService:
    """A service for synthesizing speech using the Kokoro TTS model."""

    def __init__(self, voice_model="af_heart"):
        # The user must ensure this model is downloaded and available.
        # This path structure is an assumption based on Coqui TTS standards.
        model_path = f"tts_models/en/vctk/{voice_model}"
        vocoder_path = "vocoder_models/en/ljspeech/hifigan_v2"
        print(f"Loading TTS model: {model_path}")
        try:
            self.tts_engine = TTS(model_path=model_path, vocoder_path=vocoder_path, progress_bar=False)
        except Exception as e:
            print(f"Error: Could not load TTS model. Ensure the voice model '{voice_model}' is correctly placed at '{model_path}'.")
            raise e

    def speak(self, text):
        """Synthesizes the given text and plays it as audio."""
        if not text: return
        print(f"🔊 Speaking: {text}")
        try:
            wav_data = self.tts_engine.tts(text)
            audio_bytes = (np.array(wav_data) * 32767).astype(np.int16).tobytes()
            pa = pyaudio.PyAudio()
            stream = pa.open(format=pyaudio.paInt16, channels=1, rate=22050, output=True) # Kokoro default rate is 22050
            stream.write(audio_bytes)
            stream.stop_stream(); stream.close(); pa.terminate()
        except Exception as e:
            print(f"Error during TTS playback: {e}")
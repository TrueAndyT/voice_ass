import os
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

# Suppress specific warnings
import warnings
warnings.filterwarnings("ignore", message="dropout option adds dropout after all but last recurrent layer")
warnings.filterwarnings("ignore", message=".*weight_norm.* is deprecated")
warnings.filterwarnings("ignore", message="FutureWarning")

import torch
from kokoro import KPipeline
import sounddevice as sd
import numpy as np
import threading
import queue
import time
import re
from .logger import app_logger
from .exceptions import TTSException

class TTSService:
    """TTS using Kokoro with pre-buffered chunk streaming and seamless playback."""

    def __init__(self, voice_model='af_heart'):
        self.log = app_logger.get_logger("tts_service")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.log.info(f"Initializing TTS service using device: {self.device}")
        self.voice_model = voice_model
        self.sample_rate = 24000
        self.pipeline = self._build_pipeline()
        self._stream = None

    def _build_pipeline(self):
        # Suppress the repo_id warning by explicitly passing it
        return KPipeline(lang_code='a', device=self.device, repo_id='hexgrad/Kokoro-82M')


    def speak(self, text):
        self.log.debug(f"Speaking: '{text}'")
        
        chunks = self._segment_text(text)
        chunk_queue = queue.Queue()

        def generate_audio(chunk, out_queue):
            try:
                generator = self.pipeline(chunk, voice=self.voice_model)
                audio_frames = []
                for _, _, audio in generator:
                    if isinstance(audio, torch.Tensor):
                        audio_np = audio.detach().cpu().numpy()
                        del audio
                        torch.cuda.empty_cache()
                    else:
                        audio_np = audio

                    if audio_np.dtype != np.float32:
                        audio_np = audio_np.astype(np.float32) / np.iinfo(audio_np.dtype).max

                    audio_frames.append(audio_np)
                full_audio = np.concatenate(audio_frames)
                out_queue.put(full_audio)
            except Exception as e:
                self.log.error(f"TTS generator error: {e}")
                out_queue.put(None)

        try:
            self._stream = sd.OutputStream(samplerate=self.sample_rate, channels=1, dtype='float32', blocksize=256)
            self._stream.start()

            for i, chunk in enumerate(chunks):
                next_queue = queue.Queue()
                thread = threading.Thread(target=generate_audio, args=(chunk, next_queue))
                thread.start()

                audio_data = next_queue.get()
                if audio_data is not None and len(audio_data) > 0:
                    self._stream.write(audio_data)

                thread.join()

        except Exception as e:
            if "cuFFT" in str(e) or "CUDA" in str(e):
                self.log.warning("cuFFT or CUDA crash detected, attempting TTS pipeline recovery...")
                try:
                    self.pipeline = self._build_pipeline()
                    self.log.info("TTS pipeline recovered successfully")
                except Exception as rebuild_error:
                    self.log.error(f"Failed to rebuild TTS pipeline: {rebuild_error}")
            self.log.error(f"TTS playback error: {e}")
        finally:
            if self._stream:
                self._stream.stop()
                self._stream.close()
                self._stream = None

    def _segment_text(self, text, max_chars=300):
        sentences = re.split(r'(?<=[.?!])\s+', text)
        chunks, buffer = [], ""

        for sentence in sentences:
            if len(buffer) + len(sentence) > max_chars:
                if buffer:
                    chunks.append(buffer.strip())
                buffer = sentence
            else:
                buffer += " " + sentence

        if buffer:
            chunks.append(buffer.strip())

        return chunks

    def warmup(self):
        self.log.debug("Warming up TTS pipeline...")
        try:
            generator = self.pipeline(" ", voice=self.voice_model)
            for _ in generator:
                pass
            self.log.info("TTS pipeline warmed up successfully")
        except Exception as e:
            self.log.error(f"TTS warmup failed: {e}")
            raise TTSException(f"TTS warmup failed: {e}")

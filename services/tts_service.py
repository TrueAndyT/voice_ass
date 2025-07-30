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
        self.device = self._get_device()
        self.voice_model = voice_model
        self.sample_rate = 24000
        self.pipeline = self._build_pipeline()
        self._stream = None

    def _get_device(self):
        """Determine the compute device (CUDA or CPU) for TTS."""
        if torch.cuda.is_available():
            try:
                gpu_name = torch.cuda.get_device_name(0)
                gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)  # GB
                self.log.info(f"TTS (Kokoro) running on GPU: {gpu_name} ({gpu_memory:.1f}GB)")
                return "cuda"
            except Exception as e:
                self.log.warning(f"CUDA is available but failed to initialize: {e}")
                self.log.warning("TTS (Kokoro) falling back to CPU")
                return "cpu"
        else:
            self.log.warning("TTS (Kokoro) running on CPU - GPU acceleration not available")
            return "cpu"

    def _build_pipeline(self):
        # Load the model and move it to the correct device
        pipeline = KPipeline(lang_code='a', repo_id='hexgrad/Kokoro-82M')
        pipeline.model.to(self.device)
        return pipeline


    def speak(self, text):
        self.log.debug(f"Speaking: '{text}'")
        
        # Create a queue to hold generated audio chunks
        audio_queue = queue.Queue()
        
        # Use a poison pill to signal the end of generation
        POISON_PILL = None

        def audio_generation_thread(text_chunks):
            try:
                for chunk in text_chunks:
                    generator = self.pipeline(chunk, voice=self.voice_model)
                    for _, _, audio in generator:
                        if isinstance(audio, torch.Tensor):
                            audio_np = audio.detach().cpu().numpy()
                            if self.device == "cuda":
                                torch.cuda.empty_cache()
                        else:
                            audio_np = audio
                        
                        if audio_np.dtype != np.float32:
                            audio_np = audio_np.astype(np.float32) / np.iinfo(audio_np.dtype).max
                        
                        audio_queue.put(audio_np)
            except Exception as e:
                self.log.error(f"TTS generator error: {e}")
                import traceback
                self.log.error(traceback.format_exc())
            finally:
                audio_queue.put(POISON_PILL)

        # Start the audio generation thread
        text_chunks = self._segment_text(text)
        gen_thread = threading.Thread(target=audio_generation_thread, args=(text_chunks,))
        gen_thread.start()

        # Play audio from the queue
        try:
            with sd.OutputStream(samplerate=self.sample_rate, channels=1, dtype='float32') as stream:
                self.log.info("Audio stream opened successfully.")
                while True:
                    audio_chunk = audio_queue.get()
                    if audio_chunk is POISON_PILL:
                        self.log.info("Poison pill received, closing stream.")
                        break
                    stream.write(audio_chunk)
                self.log.info("Finished writing to audio stream.")
        except Exception as e:
            self.log.error(f"TTS playback failed: {e}", exc_info=True)
        finally:
            gen_thread.join() # Ensure generator thread is cleaned up

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

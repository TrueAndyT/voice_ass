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
from .utils.logger import app_logger
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


    def speak(self, text=None, chunks=None):
        if chunks is None:
            self.log.debug(f"Speaking full text: '{text}'")
            chunks = self._segment_text(text)
        else:
            self.log.debug(f"Speaking from {len(chunks)} pre-segmented chunks.")

        self.log.debug(f"Text segmented into {len(chunks)} chunks")
        for i, chunk in enumerate(chunks):
            self.log.debug(f"Chunk {i}: '{chunk[:50]}...'" if len(chunk) > 50 else f"Chunk {i}: '{chunk}'")

        def generate_audio(chunk, out_queue):
            try:
                # Use torch.no_grad() to reduce memory allocation during inference
                with torch.no_grad():
                    generator = self.pipeline(chunk, voice=self.voice_model)
                    audio_frames = []
                    for _, _, audio in generator:
                        if isinstance(audio, torch.Tensor):
                            audio_np = audio.detach().cpu().numpy()
                            del audio
                        else:
                            audio_np = audio

                        if audio_np.dtype != np.float32:
                            audio_np = audio_np.astype(np.float32) / np.iinfo(audio_np.dtype).max

                        audio_frames.append(audio_np)
                    
                    # Clear generator explicitly and empty cache
                    del generator
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                    
                    full_audio = np.concatenate(audio_frames)
                    out_queue.put(full_audio)
            except Exception as e:
                self.log.error(f"TTS generator error: {e}")
                out_queue.put(None)

        try:
            self._stream = sd.OutputStream(samplerate=self.sample_rate, channels=1, dtype='float32', blocksize=256)
            self._stream.start()

            # Process all chunks
            for i, chunk in enumerate(chunks):
                chunk_queue = queue.Queue()
                thread = threading.Thread(target=generate_audio, args=(chunk, chunk_queue))
                thread.start()

                audio_data = chunk_queue.get()
                if audio_data is not None and len(audio_data) > 0:
                    self.log.debug(f"Playing chunk {i} with {len(audio_data)} samples")
                    self._stream.write(audio_data)
                else:
                    self.log.warning(f"Chunk {i} returned no audio data")

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

    def _segment_text(self, text, max_chars=200):  # Reduced for better memory management
        # First try to split by sentences
        sentences = re.split(r'(?<=[.?!])\s+', text)
        chunks, buffer = [], ""

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # If single sentence is too long, split by commas or clauses
            if len(sentence) > max_chars:
                # Split long sentences by commas or semicolons
                sub_parts = re.split(r'(?<=[,;])\s+', sentence)
                for part in sub_parts:
                    part = part.strip()
                    if len(buffer) + len(part) + 1 > max_chars:
                        if buffer:
                            chunks.append(buffer.strip())
                        buffer = part
                    else:
                        if buffer:
                            buffer += " " + part
                        else:
                            buffer = part
            else:
                # Normal sentence processing
                if len(buffer) + len(sentence) + 1 > max_chars:
                    if buffer:
                        chunks.append(buffer.strip())
                    buffer = sentence
                else:
                    if buffer:
                        buffer += " " + sentence
                    else:
                        buffer = sentence

        if buffer:
            chunks.append(buffer.strip())

        # Log chunk details for debugging
        self.log.debug(f"Text segmented into {len(chunks)} chunks (max {max_chars} chars each)")
        for i, chunk in enumerate(chunks[:3]):  # Log first 3 chunks only
            self.log.debug(f"Chunk {i}: '{chunk[:100]}{'...' if len(chunk) > 100 else ''}'")

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

    def stream_speak(self, chunk_iterator):
        """Speak using streaming chunks."""
        self.log.info("Starting streaming TTS...")
        try:
            self._stream = sd.OutputStream(samplerate=self.sample_rate, channels=1, dtype='float32', blocksize=256)
            self._stream.start()

            for chunk in chunk_iterator:
                self.log.debug(f"Received text chunk: {chunk[:50]}...")
                audio_data = self._generate_chunk_audio(chunk)
                if audio_data is not None and len(audio_data) > 0:
                    self.log.debug(f"Playing chunk with {len(audio_data)} samples")
                    self._stream.write(audio_data)
                else:
                    self.log.warning("Chunk returned no audio data")

        except Exception as e:
            self.log.error(f"TTS streaming playback error: {e}")
        finally:
            if self._stream:
                self._stream.stop()
                self._stream.close()
                self._stream = None

    def _generate_chunk_audio(self, chunk):
        """Generate audio for a text chunk."""
        def generate_audio(chunk, out_queue):
            try:
                # Use torch.no_grad() to reduce memory allocation during inference
                with torch.no_grad():
                    generator = self.pipeline(chunk, voice=self.voice_model)
                    audio_frames = []
                    for _, _, audio in generator:
                        if isinstance(audio, torch.Tensor):
                            audio_np = audio.detach().cpu().numpy()
                            del audio
                        else:
                            audio_np = audio

                        if audio_np.dtype != np.float32:
                            audio_np = audio_np.astype(np.float32) / np.iinfo(audio_np.dtype).max

                        audio_frames.append(audio_np)
                    
                    # Clear generator explicitly and empty cache
                    del generator
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                    
                    full_audio = np.concatenate(audio_frames)
                    out_queue.put(full_audio)
            except Exception as e:
                self.log.error(f"TTS generator error: {e}")
                out_queue.put(None)

        chunk_queue = queue.Queue()
        thread = threading.Thread(target=generate_audio, args=(chunk, chunk_queue))
        thread.start()

        audio_data = chunk_queue.get()
        thread.join()

        return audio_data

    def stop(self):
        """Immediately stop audio playback"""
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
            self.log.info("TTS playback stopped")

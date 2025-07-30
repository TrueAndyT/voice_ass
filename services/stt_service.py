import torch
import whisper
import pyaudio
import webrtcvad
import numpy as np
import os
import time
import logging.handlers
from datetime import datetime
from contextlib import contextmanager
from .logger import app_logger
from .exceptions import STTException, AudioException, ResourceException, VoiceAssistantException

# --- Configuration ---
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
VAD_FRAME_MS = 30
VAD_FRAME_SAMPLES = int(RATE * (VAD_FRAME_MS / 1000.0))
MAX_INT16 = 32767.0

class STTService:
    """A service for transcribing speech with Whisper, VAD, and dynamic thresholding."""

    def __init__(self, model_size="small", dynamic_rms=None):
        self.log = app_logger.get_logger("stt_service")
        self.log.info(f"Initializing STT service with model: {model_size}")
        
        self.device = self._get_device()
        self.model = self._load_model(model_size)
        self.vad = webrtcvad.Vad(3)
        self.allowed_languages = {'en', 'uk'}
        self.dynamic_rms = dynamic_rms

        # Dedicated logger for transcriptions
        self.transcription_logger = self._setup_transcription_logger()

    def _get_device(self):
        """Determine the compute device (CUDA or CPU)."""
        if torch.cuda.is_available():
            try:
                gpu_name = torch.cuda.get_device_name(0)
                gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)  # GB
                self.log.info(f"STT (Whisper) running on GPU: {gpu_name} ({gpu_memory:.1f}GB)")
                return "cuda"
            except Exception as e:
                self.log.warning(f"CUDA is available but failed to initialize: {e}")
                self.log.warning("STT (Whisper) falling back to CPU")
                return "cpu"
        else:
            self.log.warning("STT (Whisper) running on CPU - GPU acceleration not available")
            return "cpu"

    def _load_model(self, model_size):
        """Load the Whisper ASR model with error handling."""
        try:
            self.log.info(f"Loading Whisper model: {model_size}")
            model = whisper.load_model(model_size, device=self.device)
            self.log.info("Whisper model loaded successfully")
            return model
        except Exception as e:
            raise ResourceException(
                f"Failed to load Whisper model: {model_size}",
                context={"device": self.device, "error": str(e)}
            )

    def _setup_transcription_logger(self):
        """Set up a dedicated logger for STT transcriptions."""
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        
        logger = app_logger.get_logger("transcriptions")
        logger.propagate = False # Prevent double logging
        
        # Remove default handlers if any
        if logger.hasHandlers():
            logger.handlers.clear()
            
        # Create a file handler that rotates daily
        handler = logging.handlers.TimedRotatingFileHandler(
            os.path.join(log_dir, "transcriptions.log"), 
            when='D', interval=1, backupCount=7
        )
        handler.setFormatter(logging.Formatter("%(asctime)s: %(message)s"))
        logger.addHandler(handler)
        
        return logger

    def _write_transcription_to_log(self, text):
        """Save the transcription to a dedicated rotating log file."""
        try:
            self.transcription_logger.info(text)
        except Exception as e:
            self.log.error(f"Failed to write transcription to log: {e}")

    def listen_and_transcribe(self, timeout_ms=3000):
        """Listen for audio, record until silence, and transcribe with robust error handling."""
        try:
            with self._audio_stream_manager() as stream:
                self.log.debug("Listening for command...")
                
                recorded_frames = self._record_audio(stream, timeout_ms)
                audio_data = b''.join(recorded_frames)
                
                self.log.info("Transcription started")
                start_time = time.time()
                
                transcription = self._transcribe_audio(audio_data)
                
                duration = time.time() - start_time
                app_logger.log_performance("stt_transcription", duration, {
                    "audio_duration_ms": len(audio_data) * 1000 // (RATE * 2), # 16-bit
                    "transcription_length": len(transcription)
                })
                
                if transcription:
                    self._write_transcription_to_log(transcription)
                
                return transcription
                
        except VoiceAssistantException:
            raise # Propagate known exceptions
        except Exception as e:
            raise STTException(
                f"An unexpected error occurred during transcription: {e}",
                context={"error_type": type(e).__name__}
            ) from e

    @contextmanager
    def _audio_stream_manager(self):
        """Context manager for PyAudio stream."""
        pa = pyaudio.PyAudio()
        stream = None
        try:
            stream = pa.open(
                format=FORMAT, channels=CHANNELS, rate=RATE, 
                input=True, frames_per_buffer=VAD_FRAME_SAMPLES
            )
            yield stream
        except OSError as e:
            raise AudioException(
                f"Could not open microphone stream: {e}", 
                recoverable=False
            )
        finally:
            if stream and stream.is_active():
                stream.stop_stream()
                stream.close()
            pa.terminate()

    def _record_audio(self, stream, timeout_ms):
        """Record audio from the stream until silence is detected."""
        recorded_frames = []
        silence_duration_ms = 0
        threshold = self.dynamic_rms.get_threshold() if self.dynamic_rms else 0.15
        
        self.log.debug(f"Using VAD threshold: {threshold:.2f}")

        while True:
            try:
                audio_chunk = stream.read(VAD_FRAME_SAMPLES, exception_on_overflow=False)
                recorded_frames.append(audio_chunk)

                chunk_np = np.frombuffer(audio_chunk, dtype=np.int16)
                normalized_chunk = chunk_np.astype(np.float32) / MAX_INT16
                rms = np.sqrt(np.mean(normalized_chunk**2))
                is_speech = self.vad.is_speech(audio_chunk, sample_rate=RATE) and (rms > threshold)

                if is_speech:
                    if self.dynamic_rms:
                        self.dynamic_rms.lock()
                    silence_duration_ms = 0
                else:
                    silence_duration_ms += VAD_FRAME_MS
                    if silence_duration_ms >= timeout_ms:
                        self.log.debug("Silence detected, processing audio")
                        break
            except IOError as e:
                raise AudioException(f"Error reading from audio stream: {e}")

        return recorded_frames

    def _transcribe_audio(self, audio_data):
        """Transcribe the collected audio data using Whisper."""
        audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / MAX_INT16
        
        if len(audio_np) < RATE * 0.5: # 0.5s minimum
            self.log.warning("Recording is too short, skipping transcription")
            if self.dynamic_rms:
                self.dynamic_rms.reset()
            return ""

        try:
            # Force English transcription only
            result = self.model.transcribe(
                audio_np, 
                fp16=(self.device == "cuda"), 
                language='en',  # Force English language
                no_speech_threshold=0.6
            )

            transcription = result['text'].strip()
            
            if self.dynamic_rms:
                self.dynamic_rms.reset()
                
            return transcription
            
        except Exception as e:
            raise STTException(
                f"Whisper model failed to transcribe audio: {e}",
                context={"audio_length_s": len(audio_np) / RATE}
            )
    
    def transcribe_audio_bytes(self, audio_bytes):
        """Transcribe audio from raw bytes (for microservice API)."""
        try:
            # Convert bytes to numpy array
            audio_np = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / MAX_INT16
            
            if len(audio_np) < RATE * 0.5:  # 0.5s minimum
                self.log.warning("Audio too short for transcription")
                return ""
            
            # Force English transcription only
            result = self.model.transcribe(
                audio_np,
                fp16=(self.device == "cuda"),
                language='en',  # Force English language
                no_speech_threshold=0.6
            )
            
            transcription = result['text'].strip()
            
            if transcription:
                self._write_transcription_to_log(transcription)
            
            return transcription
            
        except Exception as e:
            raise STTException(
                f"Failed to transcribe audio bytes: {e}",
                context={"audio_bytes_length": len(audio_bytes)}
            )

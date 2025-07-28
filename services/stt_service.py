import torch
import whisper
import pyaudio
import webrtcvad
import numpy as np
import os
from datetime import datetime
import logging # <-- Import logging
from logging.handlers import TimedRotatingFileHandler # <-- Import the handler

# --- Configuration ---
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
VAD_FRAME_MS = 30
VAD_FRAME_SAMPLES = int(RATE * (VAD_FRAME_MS / 1000.0))
MAX_INT16 = 32767.0
RMS_THRESHOLD = 0.15 

class STTService:
    """A service for transcribing speech using the Whisper ASR model."""

    def __init__(self, model_size="small"):
        if torch.cuda.is_available():
            try:
                _ = torch.cuda.get_device_name(0)
                self.device = "cuda"
            except Exception as e:
                print(f"⚠️ CUDA is available but failed to initialize: {e}")
                self.device = "cpu"
        else:
            self.device = "cpu"

        print(f"Whisper using device: {self.device}")
        self.model = whisper.load_model(model_size, device=self.device)
        self.vad = webrtcvad.Vad(3)
        self.allowed_languages = {'en', 'uk'}

        # --- NEW: Set up the dedicated STT logger ---
        self.stt_logger = self._setup_stt_logger()

    def _setup_stt_logger(self):
        """Sets up a timed rotating logger for STT transcriptions."""
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        
        logger = logging.getLogger("STTLogger")
        logger.setLevel(logging.INFO)
        logger.propagate = False # Prevent STT logs from appearing in the main app.log

        # Clear existing handlers to prevent duplicates
        if logger.hasHandlers():
            logger.handlers.clear()

        # Create a handler that rotates the log file every 2 days
        handler = TimedRotatingFileHandler(
            os.path.join(log_dir, "stt.log"), 
            when='D',       # 'D' for day
            interval=2,     # Rotate every 2 days
            backupCount=5   # Keep 5 old log files
        )
        
        # Simple formatter: just the timestamp and the message
        formatter = logging.Formatter('%(asctime)s: %(message)s')
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        return logger

    def _write_transcription_to_log(self, text):
        """Saves the transcription to the rotating log file."""
        # --- MODIFIED: Use the logger instead of writing a new file ---
        self.stt_logger.info(text)
        print("Transcription logged.")

    def listen_and_transcribe(self, timeout_ms=3000):
        """
        Listens for audio, records until silence, and transcribes.
        """
        pa = pyaudio.PyAudio()
        stream = pa.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=VAD_FRAME_SAMPLES)
        
        print("Transcription started")
        
        recorded_frames = []
        silence_duration_ms = 0

        while True:
            audio_chunk = stream.read(VAD_FRAME_SAMPLES)
            recorded_frames.append(audio_chunk)

            chunk_np = np.frombuffer(audio_chunk, dtype=np.int16)
            normalized_chunk = chunk_np.astype(np.float32) / MAX_INT16
            rms = np.sqrt(np.mean(normalized_chunk**2))
            is_speech = self.vad.is_speech(audio_chunk, sample_rate=RATE) and (rms > RMS_THRESHOLD)

            if not is_speech:
                silence_duration_ms += VAD_FRAME_MS
                if silence_duration_ms >= timeout_ms:
                    print("Silence detected, processing command...")
                    break
            else:
                silence_duration_ms = 0

        print("Transcription ended")

        stream.stop_stream()
        stream.close()
        pa.terminate()
        
        print("🤖 Transcribing...")
        audio_data = b''.join(recorded_frames)
        audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / MAX_INT16
        
        if len(audio_np) < RATE * 0.5:
            print("Recording too short, skipping transcription.")
            return ""

        result = self.model.transcribe(
            audio_np, 
            fp16=(self.device=="cuda"), 
            no_speech_threshold=0.6
        )
        
        detected_language = result.get('language')
        if detected_language not in self.allowed_languages:
            print(f"Detected language '{detected_language}' is not supported. Forcing transcription to English as a fallback.")
            result = self.model.transcribe(
                audio_np, 
                fp16=(self.device=="cuda"), 
                language='en',
                no_speech_threshold=0.6
            )

        transcription = result['text'].strip()
        
        if transcription:
            self._write_transcription_to_log(transcription)
        
        return transcription
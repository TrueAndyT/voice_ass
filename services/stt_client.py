#!/usr/bin/env python3
"""
HTTP client for the STT microservice.
Provides the same interface as the original STT service but communicates via HTTP.
"""

import requests
import time
import io
import pyaudio
import webrtcvad
import numpy as np
from contextlib import contextmanager
from .logger import app_logger
from .exceptions import STTException, AudioException

# --- Configuration ---
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
VAD_FRAME_MS = 30
VAD_FRAME_SAMPLES = int(RATE * (VAD_FRAME_MS / 1000.0))
MAX_INT16 = 32767.0

class STTClient:
    """HTTP client for STT microservice that mimics the original STT service interface."""
    
    def __init__(self, host="127.0.0.1", port=8002, timeout=60, dynamic_rms=None):
        self.log = app_logger.get_logger("stt_client")
        self.base_url = f"http://{host}:{port}"
        self.timeout = timeout
        self.dynamic_rms = dynamic_rms
        self.vad = webrtcvad.Vad(3)
        self.log.info(f"STT client initialized for {self.base_url}")
    
    def listen_and_transcribe(self, timeout_ms=3000):
        """Listen for audio, record until silence, then send to STT microservice for transcription."""
        try:
            with self._audio_stream_manager() as stream:
                self.log.debug("Listening for command...")
                
                recorded_frames = self._record_audio(stream, timeout_ms)
                audio_data = b''.join(recorded_frames)
                
                if not audio_data:
                    return ""
                
                start_time = time.time()
                transcription = self._send_for_transcription(audio_data)
                
                duration = time.time() - start_time
                app_logger.log_performance("stt_client_transcription", duration, {
                    "audio_duration_ms": len(audio_data) * 1000 // (RATE * 2),
                    "transcription_length": len(transcription)
                })
                
                return transcription
                
        except Exception as e:
            error_msg = f"STT client error during listen_and_transcribe: {e}"
            self.log.error(error_msg)
            raise STTException(error_msg) from e
    
    def _send_for_transcription(self, audio_data):
        """Send audio data to STT microservice for transcription."""
        try:
            # Create file-like object from audio data
            audio_file = io.BytesIO(audio_data)
            
            response = requests.post(
                f"{self.base_url}/transcribe",
                files={"audio": ("audio.raw", audio_file, "application/octet-stream")},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                transcription = result.get("transcription", "")
                self.log.debug(f"STT transcription completed: '{transcription}'")
                return transcription
            else:
                error_msg = f"STT transcribe request failed: {response.status_code} - {response.text}"
                self.log.error(error_msg)
                raise STTException(error_msg)
                
        except requests.exceptions.RequestException as e:
            error_msg = f"STT service communication error: {e}"
            self.log.error(error_msg)
            raise STTException(error_msg) from e
    
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
    
    def health_check(self):
        """Check if the STT microservice is responsive."""
        try:
            response = requests.get(f"{self.base_url}/docs", timeout=5)
            return response.status_code == 200
        except:
            return False

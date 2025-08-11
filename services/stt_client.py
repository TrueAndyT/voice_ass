#!/usr/bin/env python3
"""
HTTP client for the STT microservice.
Provides the same interface as the original STT service but communicates via HTTP.
"""

import requests
import time
import io
from .utils.logger import app_logger
from .exceptions import STTException

class STTClient:
    """HTTP client for STT microservice that mimics the original STT service interface."""
    
    def __init__(self, host="127.0.0.1", port=8002, timeout=60, dynamic_rms=None):
        self.log = app_logger.get_logger("stt_client")
        self.base_url = f"http://{host}:{port}"
        self.timeout = timeout
        self.dynamic_rms = dynamic_rms
        self.log.debug(f"STT client initialized for {self.base_url}")
    
    def listen_and_transcribe(self, timeout_ms=3000):
        """Deprecated: This method creates audio conflicts. Use transcribe_audio_bytes instead."""
        self.log.error("listen_and_transcribe() creates PyAudio conflicts in microservices architecture")
        raise STTException("listen_and_transcribe() is not supported in microservices mode. Use transcribe_audio_bytes() instead.")
    
    def transcribe_audio_bytes(self, audio_data):
        """Send pre-recorded audio data to STT microservice for transcription."""
        try:
            if not audio_data:
                return ""
                
            start_time = time.time()
            transcription = self._send_for_transcription(audio_data)
            
            duration = time.time() - start_time
            app_logger.log_performance("stt_client_transcription", duration, {
                "audio_duration_ms": len(audio_data) * 1000 // (16000 * 2),  # 16kHz * 2 bytes per sample
                "transcription_length": len(transcription)
            })
            
            return transcription
            
        except Exception as e:
            error_msg = f"STT client error during transcribe_audio_bytes: {e}"
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
    
    
    def health_check(self):
        """Check if the STT microservice is responsive."""
        try:
            response = requests.get(f"{self.base_url}/docs", timeout=5)
            return response.status_code == 200
        except:
            return False

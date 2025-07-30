#!/usr/bin/env python3
"""
HTTP client for the TTS microservice.
Provides the same interface as the original TTS service but communicates via HTTP.
"""

import requests
import time
from .logger import app_logger
from .exceptions import TTSException

class TTSClient:
    """HTTP client for TTS microservice that mimics the original TTS service interface."""
    
    def __init__(self, host="127.0.0.1", port=8001, timeout=30):
        self.log = app_logger.get_logger("tts_client")
        self.base_url = f"http://{host}:{port}"
        self.timeout = timeout
        self.log.debug(f"TTS client initialized for {self.base_url}")
    
    def speak(self, text):
        """Send text to TTS microservice for speech synthesis."""
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/speak",
                json={"text": text},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                duration = time.time() - start_time
                self.log.debug(f"TTS speak request completed in {duration:.2f}s")
                return response.json()
            else:
                error_msg = f"TTS speak request failed: {response.status_code} - {response.text}"
                self.log.error(error_msg)
                raise TTSException(error_msg)
                
        except requests.exceptions.RequestException as e:
            error_msg = f"TTS service communication error: {e}"
            self.log.error(error_msg)
            raise TTSException(error_msg) from e
    
    def warmup(self):
        """Send warmup request to TTS microservice."""
        try:
            response = requests.post(
                f"{self.base_url}/warmup",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                self.log.debug("TTS service warmed up successfully")
                return response.json()
            else:
                error_msg = f"TTS warmup request failed: {response.status_code} - {response.text}"
                self.log.error(error_msg)
                raise TTSException(error_msg)
                
        except requests.exceptions.RequestException as e:
            error_msg = f"TTS service communication error during warmup: {e}"
            self.log.error(error_msg)
            raise TTSException(error_msg) from e
    
    def health_check(self):
        """Check if the TTS microservice is responsive."""
        try:
            response = requests.get(f"{self.base_url}/docs", timeout=5)
            return response.status_code == 200
        except:
            return False

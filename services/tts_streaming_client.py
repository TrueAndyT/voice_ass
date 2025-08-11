#!/usr/bin/env python3
"""
Enhanced TTS client with streaming support for microservices architecture.
Works with both the LLM streaming client and TTS microservice.
"""

import requests
import time
from typing import Iterator, Optional, Generator
from .utils.logger import app_logger
from .exceptions import TTSException


class TTSStreamingClient:
    """Enhanced TTS client with streaming support for real-time text-to-speech."""
    
    def __init__(self, host="127.0.0.1", port=8001, timeout=30):
        self.log = app_logger.get_logger("tts_streaming_client")
        self.base_url = f"http://{host}:{port}"
        self.timeout = timeout
        self.log.debug(f"TTS streaming client initialized for {self.base_url}")
    
    def speak(self, text: str):
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
    
    def stream_speak(self, text_stream: Iterator[str], chunk_size: int = 100):
        """
        Stream text chunks to TTS service for real-time speech synthesis.
        
        Args:
            text_stream: Iterator yielding text chunks
            chunk_size: Minimum character length before sending to TTS
        """
        try:
            buffer = ""
            chunk_count = 0
            
            self.log.info("Starting streaming TTS...")
            
            for text_chunk in text_stream:
                if not text_chunk:
                    continue
                    
                buffer += text_chunk
                
                # Send buffer to TTS when it reaches chunk_size or contains sentence endings
                if (len(buffer) >= chunk_size or 
                    any(punct in buffer for punct in ['.', '!', '?', '\n'])):
                    
                    # Find the best break point
                    break_point = self._find_break_point(buffer)
                    if break_point > 0:
                        chunk_to_speak = buffer[:break_point].strip()
                        buffer = buffer[break_point:].strip()
                        
                        if chunk_to_speak:
                            self.log.debug(f"Streaming chunk {chunk_count}: '{chunk_to_speak[:50]}...'")
                            self.speak(chunk_to_speak)
                            chunk_count += 1
            
            # Speak any remaining text in buffer
            if buffer.strip():
                self.log.debug(f"Final chunk {chunk_count}: '{buffer[:50]}...'")
                self.speak(buffer.strip())
                chunk_count += 1
            
            self.log.info(f"Streaming TTS completed with {chunk_count} chunks")
                
        except Exception as e:
            error_msg = f"Streaming TTS communication error: {e}"
            self.log.error(error_msg)
            raise TTSException(error_msg) from e
    
    def _find_break_point(self, text: str) -> int:
        """Find the best point to break text for TTS streaming."""
        # Look for sentence endings first
        for i in range(len(text) - 1, -1, -1):
            if text[i] in '.!?':
                return i + 1
        
        # Look for comma or other punctuation
        for i in range(len(text) - 1, -1, -1):
            if text[i] in ',:;':
                return i + 1
        
        # Look for word boundaries
        for i in range(len(text) - 1, -1, -1):
            if text[i] == ' ':
                return i + 1
        
        # If no good break point found, return full length
        return len(text)
    
    def stream_from_llm(self, llm_stream: Iterator[dict], text_key: str = "content"):
        """
        Stream TTS directly from LLM streaming output.
        
        Args:
            llm_stream: Iterator yielding LLM response dictionaries
            text_key: Key to extract text content from LLM response
        """
        def extract_text():
            for chunk in llm_stream:
                if isinstance(chunk, dict) and text_key in chunk:
                    yield chunk[text_key]
                elif isinstance(chunk, str):
                    yield chunk
        
        self.stream_speak(extract_text())
    
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
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False


class LLMToTTSStreamingBridge:
    """Bridge class to connect streaming LLM output directly to TTS input."""
    
    def __init__(self, tts_client: TTSStreamingClient):
        self.tts_client = tts_client
        self.log = app_logger.get_logger("llm_tts_bridge")
    
    def stream_llm_to_tts(self, llm_stream: Iterator[dict], 
                         chunk_size: int = 100,
                         text_key: str = "content"):
        """
        Stream LLM output directly to TTS with optimized chunking.
        
        Args:
            llm_stream: Iterator yielding LLM response dictionaries
            chunk_size: Minimum character length before sending to TTS
            text_key: Key to extract text content from LLM response
        """
        self.log.info("Starting LLM to TTS streaming bridge...")
        
        def text_generator():
            for chunk in llm_stream:
                if isinstance(chunk, dict):
                    if text_key in chunk and chunk[text_key]:
                        yield chunk[text_key]
                    # Log metrics if available
                    if "metrics" in chunk:
                        metrics = chunk["metrics"]
                        self.log.debug(f"LLM metrics: {metrics}")
                elif isinstance(chunk, str) and chunk:
                    yield chunk
        
        try:
            self.tts_client.stream_speak(text_generator(), chunk_size=chunk_size)
            self.log.info("LLM to TTS streaming completed successfully")
        except Exception as e:
            self.log.error(f"LLM to TTS streaming failed: {e}")
            raise


# Convenience function for easy integration
def create_streaming_tts_client(host="127.0.0.1", port=8001) -> TTSStreamingClient:
    """Create and return a configured streaming TTS client."""
    return TTSStreamingClient(host=host, port=port)


def create_llm_tts_bridge(tts_host="127.0.0.1", tts_port=8001) -> LLMToTTSStreamingBridge:
    """Create and return a configured LLM to TTS streaming bridge."""
    tts_client = create_streaming_tts_client(host=tts_host, port=tts_port)
    return LLMToTTSStreamingBridge(tts_client)

#!/usr/bin/env python3
"""
Enhanced LLM client with streaming capabilities for real-time response processing.
Supports both regular HTTP requests and Server-Sent Events (SSE) streaming.
"""

import requests
import time
import json
import sseclient
from typing import Iterator, Dict, Any, Optional, Callable
from .utils.logger import app_logger
from .exceptions import LLMException
from .handlers.intent_detector import IntentDetector


class StreamingLLMClient:
    """HTTP client for LLM microservice with streaming support."""
    
    def __init__(self, host="127.0.0.1", port=8003, timeout=120):
        self.log = app_logger.get_logger("streaming_llm_client")
        self.base_url = f"http://{host}:{port}"
        self.timeout = timeout
        self.intent_detector = IntentDetector()
        self.log.info(f"Streaming LLM client initialized for {self.base_url}")
    
    def get_response(self, prompt: str) -> tuple:
        """Get a non-streaming response (backward compatibility)."""
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/chat",
                json={"prompt": prompt},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                duration = time.time() - start_time
                self.log.debug(f"LLM chat request completed in {duration:.2f}s")
                result = response.json()
                
                llm_response = result.get("response", "")
                metrics = result.get("metrics", {})
                
                return llm_response, metrics
            else:
                error_msg = f"LLM chat request failed: {response.status_code} - {response.text}"
                self.log.error(error_msg)
                raise LLMException(error_msg)
                
        except requests.exceptions.RequestException as e:
            error_msg = f"LLM service communication error: {e}"
            self.log.error(error_msg)
            raise LLMException(error_msg) from e
    
    def get_streaming_response(self, prompt: str, chunk_threshold: int = 50, 
                             sentence_boundary: bool = True) -> Iterator[Dict[str, Any]]:
        """
        Get a streaming response from the LLM service.
        
        Args:
            prompt: User input prompt
            chunk_threshold: Minimum characters before yielding chunk
            sentence_boundary: Whether to break on sentence boundaries
            
        Yields:
            Dict containing:
            - type: 'intent', 'first_token', 'chunk', 'complete', or 'error'
            - content: Text content (if applicable)
            - other fields based on type
        """
        try:
            self.log.info(f"Starting streaming request for: '{prompt[:50]}...'")
            
            response = requests.post(
                f"{self.base_url}/chat/stream",
                json={
                    "prompt": prompt,
                    "chunk_threshold": chunk_threshold,
                    "sentence_boundary": sentence_boundary
                },
                stream=True,
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                error_msg = f"Streaming request failed: {response.status_code} - {response.text}"
                self.log.error(error_msg)
                raise LLMException(error_msg)
            
            # Process Server-Sent Events
            client = sseclient.SSEClient(response)
            
            for event in client.events():
                if event.data:
                    try:
                        data = json.loads(event.data)
                        yield data
                    except json.JSONDecodeError as e:
                        self.log.warning(f"Failed to parse SSE data: {e}")
                        continue
                        
        except requests.exceptions.RequestException as e:
            error_msg = f"Streaming communication error: {e}"
            self.log.error(error_msg)
            yield {
                'type': 'error',
                'content': error_msg,
                'is_final': True
            }
    
    def get_streaming_text(self, prompt: str, **kwargs) -> Iterator[str]:
        """
        Simplified streaming interface that yields only text chunks.
        Perfect for TTS integration.
        """
        for chunk_data in self.get_streaming_response(prompt, **kwargs):
            if chunk_data.get('type') == 'chunk' and chunk_data.get('content'):
                yield chunk_data['content']
            elif chunk_data.get('type') == 'complete' and chunk_data.get('content'):
                # Yield the complete response if no chunks were sent
                content = chunk_data['content']
                if content:
                    yield content
    
    def warmup_llm(self):
        """Send warmup request to LLM microservice."""
        try:
            response = requests.post(
                f"{self.base_url}/warmup",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                self.log.debug("LLM service warmed up successfully")
                return response.json()
            else:
                error_msg = f"LLM warmup request failed: {response.status_code} - {response.text}"
                self.log.error(error_msg)
                raise LLMException(error_msg)
                
        except requests.exceptions.RequestException as e:
            error_msg = f"LLM service communication error during warmup: {e}"
            self.log.error(error_msg)
            raise LLMException(error_msg) from e
    
    def health_check(self):
        """Check if the LLM microservice is responsive."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                result = response.json()
                return result.get("status") == "healthy"
            return False
        except:
            return False


class StreamingTTSIntegration:
    """
    Integration class for streaming LLM responses directly to TTS.
    Provides minimal latency between LLM generation and TTS playback.
    """
    
    def __init__(self, llm_client: StreamingLLMClient, tts_service, 
                 min_chunk_size: int = 100, log=None):
        self.llm_client = llm_client
        self.tts_service = tts_service
        self.min_chunk_size = min_chunk_size
        self.log = log or app_logger.get_logger("streaming_tts_integration")
    
    def speak_streaming_response(self, prompt: str, 
                               chunk_callback: Optional[Callable[[str], None]] = None) -> str:
        """
        Generate streaming LLM response and immediately send chunks to TTS.
        
        Args:
            prompt: User input
            chunk_callback: Optional callback function for each chunk (for debugging/logging)
            
        Returns:
            Complete response text
        """
        self.log.info(f"Starting streaming TTS for: '{prompt[:50]}...'")
        
        buffer = ""
        complete_response = ""
        chunks_sent = 0
        first_chunk_time = None
        start_time = time.time()
        
        try:
            for chunk_data in self.llm_client.get_streaming_response(prompt):
                chunk_type = chunk_data.get('type')
                
                if chunk_type == 'first_token':
                    first_token_time = chunk_data.get('time', 0)
                    self.log.info(f"First token received in {first_token_time:.3f}s")
                
                elif chunk_type == 'chunk':
                    content = chunk_data.get('content', '')
                    if content:
                        buffer += content
                        complete_response += content
                        
                        # Send to TTS when buffer is large enough
                        if len(buffer) >= self.min_chunk_size:
                            if first_chunk_time is None:
                                first_chunk_time = time.time()
                                self.log.info("Starting TTS playback with first chunk")
                            
                            # Send chunk to TTS
                            self.tts_service.speak(buffer.strip())
                            chunks_sent += 1
                            
                            if chunk_callback:
                                chunk_callback(buffer)
                            
                            self.log.debug(f"Sent chunk {chunks_sent} to TTS: {len(buffer)} chars")
                            buffer = ""
                
                elif chunk_type == 'complete':
                    # Handle any remaining content
                    if buffer.strip():
                        self.tts_service.speak(buffer.strip())
                        chunks_sent += 1
                        
                        if chunk_callback:
                            chunk_callback(buffer)
                    
                    # Log final metrics
                    metrics = chunk_data.get('metrics', {})
                    total_time = time.time() - start_time
                    
                    self.log.info(f"Streaming TTS completed:")
                    self.log.info(f"  Total time: {total_time:.2f}s")
                    self.log.info(f"  Response length: {len(complete_response)} chars")
                    self.log.info(f"  Chunks sent to TTS: {chunks_sent}")
                    self.log.info(f"  LLM metrics: {metrics}")
                    
                    break
                
                elif chunk_type == 'error':
                    error_msg = chunk_data.get('content', 'Unknown error')
                    self.log.error(f"Streaming error: {error_msg}")
                    
                    # Try to speak whatever we have
                    if buffer.strip():
                        self.tts_service.speak(buffer.strip())
                    
                    return complete_response
            
            return complete_response
            
        except Exception as e:
            self.log.error(f"Error in streaming TTS integration: {e}")
            # Fallback: speak whatever we have
            if buffer.strip():
                self.tts_service.speak(buffer.strip())
            return complete_response


def create_streaming_integration(host="127.0.0.1", port=8003):
    """
    Factory function to create streaming LLM client and TTS integration.
    """
    from .tts_service import TTSService
    
    llm_client = StreamingLLMClient(host=host, port=port)
    tts_service = TTSService()
    
    integration = StreamingTTSIntegration(llm_client, tts_service)
    
    return llm_client, tts_service, integration


# Usage example
if __name__ == "__main__":
    # Demo streaming functionality
    client = StreamingLLMClient()
    
    print("🚀 Testing streaming LLM client...")
    
    prompt = "Tell me a short story about artificial intelligence"
    print(f"Prompt: {prompt}\n")
    
    for chunk_data in client.get_streaming_response(prompt):
        chunk_type = chunk_data.get('type')
        
        if chunk_type == 'intent':
            print(f"[Intent] {chunk_data.get('content')}")
        elif chunk_type == 'first_token':
            print(f"[First Token] {chunk_data.get('time'):.3f}s")
        elif chunk_type == 'chunk':
            print(chunk_data.get('content', ''), end='', flush=True)
        elif chunk_type == 'complete':
            print(f"\n\n[Complete] Metrics: {chunk_data.get('metrics')}")
        elif chunk_type == 'error':
            print(f"\n[Error] {chunk_data.get('content')}")

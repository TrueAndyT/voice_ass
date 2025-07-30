#!/usr/bin/env python3
"""
HTTP client for the LLM microservice.
Provides the same interface as the original LLM service but communicates via HTTP.
"""

import requests
import time
from .logger import app_logger
from .exceptions import LLMException
from .intent_detector import IntentDetector

class LLMClient:
    """HTTP client for LLM microservice that mimics the original LLM service interface."""
    
    def __init__(self, host="127.0.0.1", port=8003, timeout=120):
        self.log = app_logger.get_logger("llm_client")
        self.base_url = f"http://{host}:{port}"
        self.timeout = timeout
        self.intent_detector = IntentDetector()  # Add intent detector
        self.log.info(f"LLM client initialized for {self.base_url}")
    
    def get_response(self, prompt):
        """Send prompt to LLM microservice for a response."""
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
                
                # Extract response and metrics
                llm_response = result.get("response", "")
                metrics = result.get("metrics", {})
                
                self.log.debug(f"LLM Client received metrics: {metrics}")
                
                # Return tuple (response, metrics) for consistency with LLMService
                return llm_response, metrics
            else:
                error_msg = f"LLM chat request failed: {response.status_code} - {response.text}"
                self.log.error(error_msg)
                raise LLMException(error_msg)
                
        except requests.exceptions.RequestException as e:
            error_msg = f"LLM service communication error: {e}"
            self.log.error(error_msg)
            raise LLMException(error_msg) from e
    
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
            response = requests.get(f"{self.base_url}/docs", timeout=5)
            return response.status_code == 200
        except:
            return False

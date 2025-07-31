#!/usr/bin/env python3
"""
Comprehensive LLM service stress test with VRAM monitoring and streaming capabilities.
Tests context window limits, streaming responses, and memory management.
"""

import torch
import time
import threading
import sys
import os
import json
import ollama

# Add project root to path
sys.path.insert(0, '/home/master/Projects/test')

from services.llm_service import LLMService
from services.logger import app_logger

class LLMStressTest:
    def __init__(self):
        self.log = app_logger.get_logger("llm_stress_test")
        self.model_name = "alexa-4k"
        self.base_model = "llama3.1:8b-instruct-q4_K_M"
        
    def create_optimized_model(self):
        """Use existing optimized model with 16K context window."""
        self.log.info("Using existing optimized model with 4K context window...")
        
        try:
            # Check if model exists
            models = ollama.list()
            model_names = [model['name'] for model in models['models']]
            
            if self.model_name in model_names:
                self.log.info(f"Model {self.model_name} found and ready to use")
            else:
                self.log.warning(f"Model {self.model_name} not found, falling back to base model")
                self.model_name = self.base_model
            
        except Exception as e:
            self.log.error(f"Error checking model availability: {e}")
            # Fall back to base model
            self.model_name = self.base_model
            self.log.info(f"Using base model: {self.model_name}")
    
    def monitor_vram(self, stop_event, interval=2):
        """Monitor VRAM usage continuously using nvidia-smi."""
        import subprocess
        
        if not torch.cuda.is_available():
            self.log.warning("CUDA not available - VRAM monitoring disabled")
            return
            
        while not stop_event.is_set():
            try:
                # Use nvidia-smi to get actual GPU memory usage
                result = subprocess.run(
                    ['nvidia-smi', '--query-gpu=memory.used,memory.total', '--format=csv,noheader,nounits'],
                    capture_output=True, text=True, timeout=5
                )
                
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    if lines:
                        memory_info = lines[0].split(', ')
                        used_mb = int(memory_info[0])
                        total_mb = int(memory_info[1])
                        
                        used_gb = used_mb / 1024
                        total_gb = total_mb / 1024
                        usage_percent = (used_mb / total_mb) * 100
                        
                        self.log.info(f"GPU VRAM - Used: {used_gb:.2f}GB / {total_gb:.1f}GB ({usage_percent:.1f}%)")
                else:
                    self.log.warning(f"nvidia-smi failed: {result.stderr}")
                
            except Exception as e:
                self.log.error(f"VRAM monitoring error: {e}")
            
            # Wait for interval or stop signal
            stop_event.wait(interval)
    
    def test_streaming_response(self, prompt, max_tokens=2048):
        """Test streaming response with token-by-token output."""
        self.log.info(f"Testing streaming response for prompt: '{prompt[:50]}...'")
        
        start_time = time.time()
        total_tokens = 0
        response_text = ""
        
        try:
            # Test streaming with ollama directly
            messages = [
                {'role': 'system', 'content': 'You are Alexa, a helpful voice assistant.'},
                {'role': 'user', 'content': prompt}
            ]
            
            stream = ollama.chat(
                model=self.model_name,
                messages=messages,
                stream=True,
                options={
                    'num_predict': max_tokens,
                    'temperature': 0.7,
                    'top_p': 0.9
                }
            )
            
            first_token_time = None
            
            for chunk in stream:
                if first_token_time is None:
                    first_token_time = time.time()
                    self.log.info(f"Time to first token: {first_token_time - start_time:.3f}s")
                
                if 'message' in chunk and 'content' in chunk['message']:
                    content = chunk['message']['content']
                    response_text += content
                    total_tokens += len(content.split()) if content else 0
                    
                    # Log progress every 50 tokens
                    if total_tokens % 50 == 0 and total_tokens > 0:
                        elapsed = time.time() - start_time
                        tokens_per_sec = total_tokens / elapsed if elapsed > 0 else 0
                        self.log.debug(f"Tokens: {total_tokens}, Speed: {tokens_per_sec:.1f} tokens/s")
            
            end_time = time.time()
            total_duration = end_time - start_time
            tokens_per_sec = total_tokens / total_duration if total_duration > 0 else 0
            
            self.log.info(f"Streaming completed - {total_tokens} tokens in {total_duration:.2f}s ({tokens_per_sec:.1f} tokens/s)")
            
            return {
                'response': response_text,
                'total_tokens': total_tokens,
                'total_duration': total_duration,
                'tokens_per_second': tokens_per_sec,
                'time_to_first_token': first_token_time - start_time if first_token_time else 0
            }
            
        except Exception as e:
            self.log.error(f"Streaming test failed: {e}")
            return None
    
    def test_context_window_limits(self):
        """Test the context window limits with progressively larger inputs."""
        self.log.info("Testing context window limits...")
        
        # Generate increasingly large contexts
        test_sizes = [1000, 5000, 10000, 20000, 30000]  # Token approximations
        
        base_text = "This is a comprehensive test of the context window limits. " * 100
        
        results = []
        
        for size in test_sizes:
            # Create prompt of approximate size
            multiplier = max(1, size // len(base_text.split()))
            test_prompt = (base_text * multiplier)[:size * 4]  # Rough char to token conversion
            
            self.log.info(f"Testing context size: ~{size} tokens ({len(test_prompt)} characters)")
            
            try:
                result = self.test_streaming_response(
                    f"Please summarize the following text in 2-3 sentences: {test_prompt}",
                    max_tokens=200
                )
                
                if result:
                    results.append({
                        'context_size': size,
                        'success': True,
                        'tokens_per_second': result['tokens_per_second'],
                        'total_duration': result['total_duration']
                    })
                    self.log.info(f"✓ Context size {size} tokens: SUCCESS")
                else:
                    results.append({
                        'context_size': size,
                        'success': False
                    })
                    self.log.warning(f"✗ Context size {size} tokens: FAILED")
                    
            except Exception as e:
                self.log.error(f"Context size {size} tokens failed: {e}")
                results.append({
                    'context_size': size,
                    'success': False,
                    'error': str(e)
                })
        
        return results
    
    def test_llm_service_integration(self):
        """Test LLMService class with streaming capabilities."""
        self.log.info("Testing LLMService integration...")
        
        try:
            # Initialize LLM service with our optimized model
            llm_service = LLMService(model=self.model_name)
            
            test_prompts = [
                "What is the capital of France?",
                "Explain quantum computing in simple terms.",
                "Write a short story about a robot learning to paint. Make it detailed and engaging.",
                "Analyze the pros and cons of renewable energy sources. Be comprehensive."
            ]
            
            results = []
            
            for i, prompt in enumerate(test_prompts):
                self.log.info(f"Testing prompt {i+1}/{len(test_prompts)}: '{prompt[:50]}...'")
                
                start_time = time.time()
                response_data = llm_service.get_response(prompt)
                
                # Handle tuple return (response, metrics)
                if isinstance(response_data, tuple):
                    response, metrics = response_data
                else:
                    response = response_data
                    metrics = {}
                
                duration = time.time() - start_time
                
                result = {
                    'prompt': prompt,
                    'response_length': len(response) if response else 0,
                    'duration': duration,
                    'metrics': metrics,
                    'success': bool(response)
                }
                
                results.append(result)
                
                self.log.info(f"Response: {len(response)} chars in {duration:.2f}s")
                if metrics:
                    self.log.info(f"Metrics: {metrics}")
            
            return results
            
        except Exception as e:
            self.log.error(f"LLMService integration test failed: {e}")
            return None
    
    def run_comprehensive_test(self):
        """Run all tests with VRAM monitoring."""
        self.log.info("Starting comprehensive LLM stress test...")
        
        # Start VRAM monitoring
        stop_monitoring = threading.Event()
        monitor_thread = None
        
        if torch.cuda.is_available():
            monitor_thread = threading.Thread(
                target=self.monitor_vram,
                args=(stop_monitoring, 3)  # Monitor every 3 seconds
            )
            monitor_thread.start()
            self.log.info("VRAM monitoring started")
        
        try:
            # Create optimized model
            self.create_optimized_model()
            
            # Test 1: Context window limits
            self.log.info("=== TEST 1: Context Window Limits ===")
            context_results = self.test_context_window_limits()
            
            # Test 2: Streaming responses
            self.log.info("=== TEST 2: Streaming Responses ===")
            streaming_results = []
            
            streaming_prompts = [
                "Write a detailed explanation of machine learning algorithms.",
                "Create a comprehensive guide to Python programming for beginners.",
                "Explain the history of artificial intelligence in detail."
            ]
            
            for prompt in streaming_prompts:
                result = self.test_streaming_response(prompt, max_tokens=1000)
                if result:
                    streaming_results.append(result)
            
            # Test 3: LLMService integration
            self.log.info("=== TEST 3: LLMService Integration ===")
            service_results = self.test_llm_service_integration()
            
            # Generate comprehensive report
            self.generate_report(context_results, streaming_results, service_results)
            
        except Exception as e:
            self.log.error(f"Comprehensive test failed: {e}")
            
        finally:
            # Stop VRAM monitoring
            if monitor_thread:
                stop_monitoring.set()
                monitor_thread.join()
                self.log.info("VRAM monitoring stopped")
    
    def generate_report(self, context_results, streaming_results, service_results):
        """Generate comprehensive test report."""
        self.log.info("=== COMPREHENSIVE TEST REPORT ===")
        
        # Context window results
        self.log.info("Context Window Test Results:")
        for result in context_results:
            status = "✓ SUCCESS" if result['success'] else "✗ FAILED"
            self.log.info(f"  {result['context_size']} tokens: {status}")
            if result['success']:
                self.log.info(f"    Speed: {result['tokens_per_second']:.1f} tokens/s")
        
        # Streaming results
        if streaming_results:
            self.log.info("Streaming Response Results:")
            avg_speed = sum(r['tokens_per_second'] for r in streaming_results) / len(streaming_results)
            avg_first_token = sum(r['time_to_first_token'] for r in streaming_results) / len(streaming_results)
            self.log.info(f"  Average speed: {avg_speed:.1f} tokens/s")
            self.log.info(f"  Average time to first token: {avg_first_token:.3f}s")
        
        # Service integration results
        if service_results:
            self.log.info("LLMService Integration Results:")
            successful = sum(1 for r in service_results if r['success'])
            self.log.info(f"  Successful responses: {successful}/{len(service_results)}")
            if successful > 0:
                avg_duration = sum(r['duration'] for r in service_results if r['success']) / successful
                self.log.info(f"  Average response time: {avg_duration:.2f}s")

def main():
    """Run the LLM stress test."""
    test = LLMStressTest()
    test.run_comprehensive_test()

if __name__ == "__main__":
    main()

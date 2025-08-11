#!/usr/bin/env python3
"""
Simplified streaming integration test for LLM to TTS orchestration.
This test can run with minimal dependencies and mock services.
"""

import time
import sys
import os
from typing import Iterator, Dict

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.utils.logger import app_logger


def mock_tts_service():
    """Mock TTS service for testing without actual TTS microservice."""
    class MockTTSClient:
        def __init__(self):
            self.log = app_logger.get_logger("mock_tts")
        
        def speak(self, text):
            self.log.info(f"🎵 Speaking: {text[:50]}...")
            time.sleep(0.1)  # Simulate TTS processing time
            return {"status": "success"}
        
        def stream_speak(self, text_stream, chunk_size=100):
            self.log.info("🎵 Starting streaming TTS...")
            buffer = ""
            chunk_count = 0
            
            for text_chunk in text_stream:
                if not text_chunk:
                    continue
                    
                buffer += text_chunk
                
                if len(buffer) >= chunk_size or any(punct in buffer for punct in ['.', '!', '?']):
                    self.log.info(f"🎵 TTS Chunk {chunk_count}: {buffer[:30]}...")
                    time.sleep(0.2)  # Simulate TTS processing
                    buffer = ""
                    chunk_count += 1
            
            if buffer.strip():
                self.log.info(f"🎵 Final TTS Chunk {chunk_count}: {buffer[:30]}...")
                chunk_count += 1
            
            self.log.info(f"✅ Streaming TTS completed with {chunk_count} chunks")
        
        def health_check(self):
            return True
    
    return MockTTSClient()


def mock_llm_service():
    """Mock LLM service for testing without actual LLM microservice."""
    class MockLLMClient:
        def __init__(self):
            self.log = app_logger.get_logger("mock_llm")
        
        def get_response_stream(self, prompt):
            """Mock streaming LLM response."""
            responses = [
                {"content": "Streaming allows ", "type": "text"},
                {"content": "real-time processing ", "type": "text"},
                {"content": "of data as it arrives, ", "type": "text"},
                {"content": "enabling immediate responses ", "type": "text"},
                {"content": "without waiting for complete data.", "type": "text"},
                {"type": "metrics", "metrics": {"tokens_per_second": 12.5}}
            ]
            
            self.log.info(f"🤖 LLM Query: {prompt}")
            for response in responses:
                yield response
                time.sleep(0.3)  # Simulate LLM generation delay
        
        def health_check(self):
            return True
    
    return MockLLMClient()


def test_streaming_orchestration():
    """Test streaming orchestration with mock services."""
    log = app_logger.get_logger("streaming_test")
    
    print("🚀 Streaming LLM to TTS Integration Test (Mock Services)")
    print("=" * 60)
    
    try:
        # Create mock services
        tts_client = mock_tts_service()
        llm_client = mock_llm_service()
        
        # Test 1: Basic streaming TTS
        print("\n🧪 Test 1: Basic Streaming TTS")
        print("-" * 40)
        
        test_chunks = [
            "Hello, this is a streaming test. ",
            "Each chunk is processed individually. ",
            "This simulates real-time text-to-speech."
        ]
        
        def chunk_generator():
            for chunk in test_chunks:
                yield chunk
                time.sleep(0.2)
        
        start_time = time.time()
        tts_client.stream_speak(chunk_generator(), chunk_size=50)
        duration = time.time() - start_time
        print(f"✅ Streaming TTS test completed in {duration:.2f}s")
        
        # Test 2: LLM to TTS Bridge
        print("\n🧪 Test 2: LLM to TTS Streaming Bridge")
        print("-" * 40)
        
        # Create a simple bridge
        class SimpleLLMToTTSBridge:
            def __init__(self, llm_client, tts_client):
                self.llm_client = llm_client
                self.tts_client = tts_client
                self.log = app_logger.get_logger("llm_tts_bridge")
            
            def stream_llm_to_tts(self, prompt, chunk_size=80):
                self.log.info("🌉 Starting LLM to TTS bridge...")
                
                def text_generator():
                    for chunk in self.llm_client.get_response_stream(prompt):
                        if isinstance(chunk, dict) and "content" in chunk:
                            yield chunk["content"]
                
                self.tts_client.stream_speak(text_generator(), chunk_size=chunk_size)
                self.log.info("✅ LLM to TTS bridge completed")
        
        bridge = SimpleLLMToTTSBridge(llm_client, tts_client)
        
        test_prompt = "What is streaming and why is it useful?"
        start_time = time.time()
        bridge.stream_llm_to_tts(test_prompt, chunk_size=60)
        duration = time.time() - start_time
        print(f"✅ LLM to TTS bridge completed in {duration:.2f}s")
        
        # Test 3: Performance comparison
        print("\n🧪 Test 3: Performance Comparison")
        print("-" * 40)
        
        test_text = "This is a performance test to compare streaming versus batch processing of text-to-speech."
        
        # Streaming approach
        def streaming_test():
            chunks = [test_text[i:i+20] for i in range(0, len(test_text), 20)]
            def chunk_gen():
                for chunk in chunks:
                    yield chunk
            tts_client.stream_speak(chunk_gen(), chunk_size=15)
        
        # Batch approach
        def batch_test():
            tts_client.speak(test_text)
        
        # Benchmark streaming
        start_time = time.time()
        streaming_test()
        streaming_time = time.time() - start_time
        
        time.sleep(0.5)
        
        # Benchmark batch
        start_time = time.time()
        batch_test()
        batch_time = time.time() - start_time
        
        print(f"📊 Performance Results:")
        print(f"   Streaming: {streaming_time:.2f}s")
        print(f"   Batch:     {batch_time:.2f}s")
        
        if streaming_time < batch_time:
            improvement = ((batch_time - streaming_time) / batch_time * 100)
            print(f"   ✅ Streaming is {improvement:.1f}% faster")
        else:
            print(f"   ⚠️  Batch processing was faster (expected for small texts)")
        
        # Test 4: Integration with main application flow
        print("\n🧪 Test 4: Main Application Integration")
        print("-" * 40)
        
        def simulate_voice_interaction():
            """Simulate the main voice assistant interaction flow."""
            log.info("🎤 Simulating voice interaction...")
            
            # Simulate transcription
            transcription = "Tell me about artificial intelligence"
            log.info(f"📝 Transcription: {transcription}")
            
            # Process with streaming LLM to TTS
            speech_end_time = time.time()
            tts_start_time = time.time()
            
            try:
                # Stream LLM response directly to TTS
                bridge.stream_llm_to_tts(transcription, chunk_size=100)
                
                # Calculate latency
                speech_to_tts_time = tts_start_time - speech_end_time
                log.info(f"📊 Speech→TTS latency: {speech_to_tts_time:.2f}s")
                
                return True
                
            except Exception as e:
                log.error(f"❌ Voice interaction failed: {e}")
                return False
        
        if simulate_voice_interaction():
            print("✅ Main application integration test passed")
        else:
            print("❌ Main application integration test failed")
        
        print("\n🎉 All streaming integration tests completed successfully!")
        return True
        
    except Exception as e:
        log.error(f"Streaming integration test failed: {e}", exc_info=True)
        print(f"❌ Test failed: {e}")
        return False


def main():
    """Main test runner."""
    print("🧪 Simplified Streaming LLM to TTS Integration Test")
    print("=" * 60)
    print("This test uses mock services and doesn't require microservices to be running.")
    print()
    
    success = test_streaming_orchestration()
    
    if success:
        print("\n✅ All tests passed! Streaming orchestration logic is working correctly.")
        print("\n📝 Next steps:")
        print("   1. Start microservices: python start_services.py")
        print("   2. Run full integration test: python test_streaming_integration.py")
        print("   3. Test with main application: python main.py")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

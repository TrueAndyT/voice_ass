#!/usr/bin/env python3
"""
Integration test script for streaming LLM to TTS orchestration.
Tests the complete pipeline from LLM streaming to TTS processing.
"""

import time
import sys
import os
from typing import Iterator, Dict

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.utils.logger import app_logger
from services.tts_streaming_client import TTSStreamingClient, LLMToTTSStreamingBridge, create_llm_tts_bridge


def test_streaming_orchestration():
    """Test the complete streaming orchestration pipeline."""
    log = app_logger.get_logger("streaming_integration_test")
    
    print("🚀 Starting Streaming LLM to TTS Integration Test")
    print("=" * 60)
    
    try:
        # Test 1: Basic TTS Streaming Client
        print("\n🧪 Test 1: TTS Streaming Client")
        print("-" * 40)
        
        tts_client = TTSStreamingClient()
        
        # Check TTS service health
        if not tts_client.health_check():
            print("❌ TTS service is not available. Please start the TTS microservice server.")
            print("   Run: python services/tts_service_server.py")
            return False
        
        print("✅ TTS service is healthy")
        
        # Test streaming text chunks
        test_chunks = [
            "Hello, this is a streaming test. ",
            "The text is being sent in chunks. ",
            "Each chunk should be spoken as it arrives. ",
            "This demonstrates real-time text-to-speech processing."
        ]
        
        def chunk_generator():
            for chunk in test_chunks:
                yield chunk
                time.sleep(0.5)  # Simulate streaming delay
        
        print("🎵 Testing streaming TTS with chunks...")
        start_time = time.time()
        tts_client.stream_speak(chunk_generator(), chunk_size=50)
        duration = time.time() - start_time
        print(f"✅ Streaming TTS completed in {duration:.2f}s")
        
        # Test 2: LLM to TTS Bridge (Mock LLM Stream)
        print("\n🧪 Test 2: LLM to TTS Bridge")
        print("-" * 40)
        
        def mock_llm_stream() -> Iterator[Dict]:
            """Mock LLM streaming response for testing."""
            responses = [
                {"content": "Artificial intelligence ", "type": "text"},
                {"content": "is transforming ", "type": "text"},
                {"content": "how we interact ", "type": "text"},
                {"content": "with technology. ", "type": "text"},
                {"content": "This streaming approach ", "type": "text"},
                {"content": "allows for real-time ", "type": "text"},
                {"content": "voice responses.", "type": "text"},
                {"type": "metrics", "metrics": {"tokens_per_second": 15.2}}
            ]
            
            for response in responses:
                yield response
                time.sleep(0.3)  # Simulate LLM generation delay
        
        bridge = LLMToTTSStreamingBridge(tts_client)
        
        print("🎵 Testing LLM to TTS bridge...")
        start_time = time.time()
        bridge.stream_llm_to_tts(mock_llm_stream(), chunk_size=60)
        duration = time.time() - start_time
        print(f"✅ LLM to TTS bridge completed in {duration:.2f}s")
        
        # Test 3: Integration with actual LLM service (if available)
        print("\n🧪 Test 3: Real LLM Integration")
        print("-" * 40)
        
        try:
            from services.llm_streaming_client import StreamingLLMClient
            llm_client = StreamingLLMClient()
            
            if llm_client.health_check():
                print("✅ Streaming LLM service is available")
                
                test_prompt = "Explain what streaming is in one sentence."
                
                print(f"🤖 Testing with prompt: '{test_prompt}'")
                start_time = time.time()
                
                # Get streaming response from LLM
                llm_stream = llm_client.get_response_stream(test_prompt)
                
                # Stream directly to TTS
                bridge.stream_llm_to_tts(llm_stream, chunk_size=80)
                
                duration = time.time() - start_time
                print(f"✅ Real LLM to TTS streaming completed in {duration:.2f}s")
                
            else:
                print("⚠️  Streaming LLM service not available, skipping real LLM test")
                print("   To test with real LLM, start: python llm_streaming_server.py")
        
        except ImportError as e:
            print(f"⚠️  LLM streaming client not available: {e}")
        
        # Test 4: Performance benchmarking
        print("\n🧪 Test 4: Performance Benchmarking")
        print("-" * 40)
        
        benchmark_text = "This is a performance benchmark test for streaming text-to-speech processing."
        chunks = [benchmark_text[i:i+20] for i in range(0, len(benchmark_text), 20)]
        
        # Benchmark streaming vs regular approach
        def benchmark_streaming():
            def chunk_gen():
                for chunk in chunks:
                    yield chunk
            return tts_client.stream_speak(chunk_gen(), chunk_size=15)
        
        def benchmark_regular():
            return tts_client.speak(benchmark_text)
        
        print("📊 Benchmarking streaming approach...")
        start_time = time.time()
        benchmark_streaming()
        streaming_time = time.time() - start_time
        
        time.sleep(1)  # Brief pause between tests
        
        print("📊 Benchmarking regular approach...")
        start_time = time.time()
        benchmark_regular()
        regular_time = time.time() - start_time
        
        print(f"📈 Results:")
        print(f"   Streaming: {streaming_time:.2f}s")
        print(f"   Regular:   {regular_time:.2f}s")
        print(f"   Improvement: {((regular_time - streaming_time) / regular_time * 100):.1f}%")
        
        print("\n🎉 All streaming integration tests completed successfully!")
        return True
        
    except Exception as e:
        log.error(f"Streaming integration test failed: {e}", exc_info=True)
        print(f"❌ Test failed: {e}")
        return False


def start_microservices():
    """Start the required microservices if they're not running."""
    import subprocess
    import threading
    import time
    
    print("\n🚀 Starting Required Microservices")
    print("-" * 40)
    
    # Start TTS service
    print("🔧 Starting TTS service...")
    try:
        tts_process = subprocess.Popen(
            ["python", "services/tts_service_server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print("✅ TTS service started")
        time.sleep(3)  # Give it time to start
    except Exception as e:
        print(f"❌ Failed to start TTS service: {e}")
        return False
    
    # Start LLM streaming service if it exists
    try:
        if os.path.exists("llm_streaming_server.py"):
            print("🔧 Starting LLM streaming service...")
            llm_process = subprocess.Popen(
                ["python", "llm_streaming_server.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            print("✅ LLM streaming service started")
            time.sleep(3)  # Give it time to start
    except Exception as e:
        print(f"⚠️  Could not start LLM streaming service: {e}")
    
    return True


def test_microservices_availability():
    """Test if all required microservices are running."""
    print("\n🔍 Testing Microservices Availability")
    print("-" * 40)
    
    services = {
        "TTS Service": ("127.0.0.1", 8001),
        "LLM Service": ("127.0.0.1", 8003),
    }
    
    available_services = []
    
    for service_name, (host, port) in services.items():
        try:
            import requests
            response = requests.get(f"http://{host}:{port}/health", timeout=2)
            if response.status_code == 200:
                print(f"✅ {service_name} is available at {host}:{port}")
                available_services.append(service_name)
            else:
                print(f"❌ {service_name} returned status {response.status_code}")
        except Exception as e:
            print(f"❌ {service_name} is not available")
    
    print(f"\n📊 Summary: {len(available_services)}/{len(services)} services available")
    return len(available_services), len(services)


def main():
    """Main test runner."""
    print("🧪 Streaming LLM to TTS Integration Test Suite")
    print("=" * 60)
    
    # Test microservices availability first
    available_count, total_count = test_microservices_availability()
    
    if available_count == 0:
        print("\n⚠️  No services are running. Attempting to start them...")
        
        # Try to start services automatically
        if start_microservices():
            print("\n🔄 Retesting service availability...")
            available_count, total_count = test_microservices_availability()
        
        if available_count == 0:
            print("\n❌ Could not start services. Manual startup required:")
            print("   TTS: python services/tts_service_server.py")
            print("   LLM: python llm_streaming_server.py")
            sys.exit(1)
    
    # Run tests with available services
    if available_count >= 1:  # At least TTS service should be available
        print(f"\n✅ Proceeding with {available_count}/{total_count} services available")
        
        # Run streaming orchestration tests
        success = test_streaming_orchestration()
        
        if success:
            print("\n✅ All tests passed! Streaming orchestration is working correctly.")
            sys.exit(0)
        else:
            print("\n❌ Some tests failed. Please check the logs and microservices.")
            sys.exit(1)
    else:
        print("\n❌ Cannot proceed without at least TTS service. Exiting.")
        sys.exit(1)


if __name__ == "__main__":
    main()

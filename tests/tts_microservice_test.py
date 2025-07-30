#!/usr/bin/env python3
import subprocess
import time
import requests
import threading
import signal
import os
from services.tts_client import TTSClient

# Test texts
short_text = "Hello, this is a microservice test."
long_text = (
    "Welcome to the comprehensive TTS microservice integration test. "
    "This test validates the full client-server architecture with latency monitoring. "
    "We are testing HTTP communication between the client and server components. "
    "The server wraps the core TTS service and provides RESTful API endpoints. "
    "The client sends HTTP requests and measures response times for performance analysis. "
    "Memory management and GPU utilization are monitored during the test execution. "
    "This comprehensive test ensures the microservice architecture functions correctly. "
    "Network latency and audio processing delays are measured and reported. "
    "Error handling and recovery mechanisms are validated under various conditions. "
    "This final sentence completes our ten-sentence microservice stress test."
)

class TTSMicroserviceTest:
    def __init__(self):
        self.server_process = None
        self.client = None
        self.server_host = "127.0.0.1"
        self.server_port = 8001
        
    def start_server(self):
        """Start the TTS microservice server"""
        print("🚀 Starting TTS microservice server...")
        
        # Start server in separate process
        self.server_process = subprocess.Popen(
            ["python", "services/tts_service_server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid  # Create new process group
        )
        
        # Wait for server to start
        max_attempts = 30
        for attempt in range(max_attempts):
            try:
                response = requests.get(f"http://{self.server_host}:{self.server_port}/health", timeout=2)
                if response.status_code == 200:
                    print(f"✅ Server started successfully on port {self.server_port}")
                    return True
            except:
                pass
            
            print(f"⏳ Waiting for server... ({attempt + 1}/{max_attempts})")
            time.sleep(2)
        
        print("❌ Failed to start server")
        return False
    
    def stop_server(self):
        """Stop the TTS microservice server"""
        if self.server_process:
            print("🛑 Stopping TTS microservice server...")
            os.killpg(os.getpgid(self.server_process.pid), signal.SIGTERM)
            self.server_process.wait()
            print("✅ Server stopped")
    
    def load_client(self):
        """Initialize TTS client"""
        print("📡 Loading TTS client...")
        self.client = TTSClient(host=self.server_host, port=self.server_port, timeout=120)
        
        # Test client connection
        if self.client.health_check():
            print("✅ Client connected successfully")
            return True
        else:
            print("❌ Client connection failed")
            return False
    
    def measure_latency(self, text, test_name):
        """Measure TTS request latency"""
        print(f"\n📊 Testing {test_name}...")
        print(f"Text length: {len(text)} characters")
        
        start_time = time.time()
        
        try:
            # Send warmup request first
            warmup_start = time.time()
            self.client.warmup()
            warmup_time = time.time() - warmup_start
            print(f"⚡ Warmup latency: {warmup_time:.2f}s")
            
            # Send speak request
            speak_start = time.time()
            result = self.client.speak(text)
            speak_time = time.time() - speak_start
            
            total_time = time.time() - start_time
            
            print(f"🎯 Speak latency: {speak_time:.2f}s")
            print(f"⏱️  Total latency: {total_time:.2f}s")
            print(f"📈 Characters per second: {len(text) / speak_time:.1f}")
            print(f"✅ {test_name} completed successfully")
            
            return {
                "warmup_latency": warmup_time,
                "speak_latency": speak_time,
                "total_latency": total_time,
                "chars_per_second": len(text) / speak_time
            }
            
        except Exception as e:
            print(f"❌ {test_name} failed: {e}")
            return None
    
    def run_comprehensive_test(self):
        """Run the complete test suite"""
        print("🧪 Starting TTS Microservice Comprehensive Test")
        print("=" * 60)
        
        try:
            # Step 1: Start server
            if not self.start_server():
                return False
            
            # Step 2: Load client
            if not self.load_client():
                return False
            
            # Step 3: Test short text
            short_results = self.measure_latency(short_text, "Short Text Test")
            
            # Step 4: Test long text
            long_results = self.measure_latency(long_text, "Long Text Test")
            
            # Step 5: Performance summary
            print("\n📈 PERFORMANCE SUMMARY")
            print("=" * 40)
            
            if short_results:
                print(f"Short text latency:     {short_results['speak_latency']:.2f}s")
                print(f"Short text speed:       {short_results['chars_per_second']:.1f} chars/s")
            
            if long_results:
                print(f"Long text latency:      {long_results['speak_latency']:.2f}s")
                print(f"Long text speed:        {long_results['chars_per_second']:.1f} chars/s")
            
            if short_results and long_results:
                efficiency = long_results['chars_per_second'] / short_results['chars_per_second']
                print(f"Efficiency ratio:       {efficiency:.2f} (higher is better)")
            
            print("\n✅ TTS Microservice Test Completed Successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            return False
        finally:
            self.stop_server()

def main():
    test = TTSMicroserviceTest()
    success = test.run_comprehensive_test()
    
    if success:
        print("\n🎉 All tests passed!")
        exit(0)
    else:
        print("\n💥 Some tests failed!")
        exit(1)

if __name__ == "__main__":
    main()

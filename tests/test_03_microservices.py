#!/usr/bin/env python3
"""
Test 3: Microservices Communication
Verifies that each microservice starts, responds to health checks, and handles a basic request.
"""

import time
import requests
import subprocess
import os


def test_microservices():
    print("\n=== Test 3: Microservices Communication ===")
    services = {
        "TTS": ("services.tts_service_server:app", 8001),
        "STT": ("services.stt_service_server:app", 8002),
        "LLM": ("services.llm_service_server:app", 8003),
    }
    
    processes = {}
    all_passed = True

    try:
        # Start all services
        for name, (app_path, port) in services.items():
            print(f"\n--- Testing {name} Microservice ---")
            command = f"python3 -m uvicorn {app_path} --host 0.0.0.0 --port {port}"
            proc = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            processes[name] = proc
            time.sleep(5) # Give it time to start

            # 1. Health Check
            try:
                url = f"http://127.0.0.1:{port}/docs"
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    print(f"1. Health Check... ✓ (Status: {response.status_code})")
                else:
                    print(f"1. Health Check... ❌ (Status: {response.status_code})")
                    all_passed = False
                    continue
            except requests.exceptions.RequestException as e:
                print(f"1. Health Check... ❌ (Error: {e})")
                all_passed = False
                continue

            # 2. Test a basic request
            print(f"2. Testing basic request...")
            if name == "TTS":
                test_data = {"text": "Hello world"}
                response = requests.post(f"http://127.0.0.1:{port}/speak", json=test_data, timeout=15)
            elif name == "STT":
                # Create a silent audio file for testing
                with open("test_audio.raw", "wb") as f:
                    f.write(os.urandom(16000 * 2)) # 1 second of audio
                with open("test_audio.raw", "rb") as f:
                    files = {"audio": ("audio.raw", f, "application/octet-stream")}
                    response = requests.post(f"http://127.0.0.1:{port}/transcribe", files=files, timeout=15)
            elif name == "LLM":
                test_data = {"prompt": "What is the capital of France?"}
                response = requests.post(f"http://127.0.0.1:{port}/chat", json=test_data, timeout=30)
            
            if response and response.status_code == 200:
                print(f"   Request successful ✓ (Status: {response.status_code})")
            else:
                print(f"   Request failed ❌ (Status: {response.status_code if response else 'N/A'})")
                all_passed = False

    finally:
        # Cleanup
        print("\n--- Cleaning up microservices ---")
        for name, proc in processes.items():
            proc.terminate()
            proc.wait()
            print(f"   {name} service stopped ✓")
            
        if all_passed:
            print("\n🎉 Test 3 PASSED: All microservices are communicating successfully!")
        else:
            print("\n❌ Test 3 FAILED: One or more microservices failed.")

if __name__ == "__main__":
    test_microservices()


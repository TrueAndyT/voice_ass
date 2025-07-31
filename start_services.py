#!/usr/bin/env python3
"""
Script to start microservices for streaming integration testing.
Starts TTS and LLM streaming services in the background.
"""

import subprocess
import time
import os
import sys
import signal
from pathlib import Path

def start_service(script_path, service_name, port):
    """Start a microservice and return the process."""
    print(f"🚀 Starting {service_name}...")
    
    try:
        # Check if the script exists
        if not os.path.exists(script_path):
            print(f"❌ {script_path} not found")
            return None
        
        # Start the service
        process = subprocess.Popen(
            [sys.executable, script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid  # Create new process group
        )
        
        # Give it time to start
        time.sleep(3)
        
        # Check if process is still running
        if process.poll() is None:
            print(f"✅ {service_name} started successfully (PID: {process.pid})")
            
            # Test if service is responding
            try:
                import requests
                response = requests.get(f"http://127.0.0.1:{port}/health", timeout=5)
                if response.status_code == 200:
                    print(f"✅ {service_name} is responding on port {port}")
                else:
                    print(f"⚠️  {service_name} started but not responding properly")
            except Exception as e:
                print(f"⚠️  {service_name} started but health check failed: {e}")
            
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"❌ {service_name} failed to start")
            if stderr:
                print(f"Error: {stderr.decode()}")
            return None
            
    except Exception as e:
        print(f"❌ Failed to start {service_name}: {e}")
        return None

def stop_services(processes):
    """Stop all running services."""
    print("\n🛑 Stopping services...")
    for name, process in processes.items():
        if process and process.poll() is None:
            try:
                # Kill the process group
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                process.wait(timeout=5)
                print(f"✅ {name} stopped")
            except Exception as e:
                print(f"⚠️  Error stopping {name}: {e}")
                try:
                    # Force kill if necessary
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                except:
                    pass

def main():
    """Main function to start services."""
    print("🚀 Starting Microservices for Streaming Integration")
    print("=" * 55)
    
    # Define services to start
    services = {
        "TTS Service": ("services/tts_service_server.py", 8001),
        "LLM Streaming Service": ("llm_streaming_server.py", 8003),
    }
    
    processes = {}
    
    try:
        # Start each service
        for service_name, (script_path, port) in services.items():
            process = start_service(script_path, service_name, port)
            if process:
                processes[service_name] = process
        
        if not processes:
            print("\n❌ No services were started successfully")
            return 1
        
        print(f"\n✅ {len(processes)} service(s) started successfully")
        print("\n📝 Services running:")
        for name in processes.keys():
            print(f"   - {name}")
        
        print("\n🧪 You can now run the integration test:")
        print("   python test_streaming_integration.py")
        
        print("\n⏹️  Press Ctrl+C to stop all services")
        
        # Keep services running
        try:
            while True:
                time.sleep(1)
                # Check if services are still running
                for name, process in list(processes.items()):
                    if process.poll() is not None:
                        print(f"⚠️  {name} has stopped unexpectedly")
                        del processes[name]
                
                if not processes:
                    print("❌ All services have stopped")
                    break
        
        except KeyboardInterrupt:
            print("\n🛑 Shutdown requested...")
        
    finally:
        stop_services(processes)
        print("👋 Services stopped")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

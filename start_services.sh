#!/bin/bash
"""
Startup script for launching all microservices.
Each service runs in its own process with dedicated resources.
"""

# Exit on any error
set -e

echo "🚀 Starting Voice Assistant Microservices..."

# Function to start a service
start_service() {
    local service_name=$1
    local script_path=$2
    local port=$3
    
    echo "Starting $service_name on port $port..."
    python3 -m uvicorn "$script_path" --host 0.0.0.0 --port "$port" &
    local pid=$!
    echo "$service_name started with PID: $pid"
    echo "$pid" > "/tmp/${service_name}.pid"
}

# Start TTS microservice
start_service "tts_service" "services.tts_service_server:app" 8001

# Add other services here as they are converted...
# start_service "stt_service" "services.stt_service_server:app" 8002
# start_service "llm_service" "services.llm_service_server:app" 8003

echo "✅ All microservices started!"
echo "📊 Check service status with: ps aux | grep uvicorn"
echo "🛑 Stop all services with: ./stop_services.sh"

# Keep script running
wait

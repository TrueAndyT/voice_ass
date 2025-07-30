#!/bin/bash
"""
Stop script for shutting down all microservices gracefully.
"""

echo "🛑 Stopping Voice Assistant Microservices..."

# Function to stop a service
stop_service() {
    local service_name=$1
    local pid_file="/tmp/${service_name}.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo "Stopping $service_name (PID: $pid)..."
            kill "$pid"
            rm -f "$pid_file"
            echo "$service_name stopped."
        else
            echo "$service_name was not running."
            rm -f "$pid_file"
        fi
    else
        echo "No PID file found for $service_name."
    fi
}

# Stop all services
stop_service "tts_service"
# stop_service "stt_service"
# stop_service "llm_service"

# Also kill any remaining uvicorn processes
echo "Cleaning up any remaining uvicorn processes..."
pkill -f "uvicorn.*services.*" || true

echo "✅ All microservices stopped!"

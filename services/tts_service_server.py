#!/usr/bin/env python3
"""
TTS microservice that provides text-to-speech functionality via an HTTP API.
"""

import sys
import os
# Insert project root at the BEGINNING of path to avoid conflicts with installed packages
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Suppress ALSA, JACK, and PulseAudio warnings in microservice
os.environ['ALSA_PCM_CARD'] = 'default'
os.environ['ALSA_PCM_DEVICE'] = '0'
os.environ['PULSE_RUNTIME_PATH'] = '/dev/null'  # Suppress PulseAudio warnings
# Redirect stderr and stdout temporarily to suppress audio warnings
original_stderr = os.dup(2)
original_stdout = os.dup(1)
os.close(2)
os.close(1)
os.open(os.devnull, os.O_RDWR)
os.open(os.devnull, os.O_RDWR)

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from services.tts_service import TTSService
from services.utils.logger import app_logger

# Restore stderr and stdout after imports
os.dup2(original_stderr, 2)
os.dup2(original_stdout, 1)
os.close(original_stderr)
os.close(original_stdout)

# Initialize FastAPI app
app = FastAPI()
log = app_logger.get_logger("tts_microservice")

# Initialize TTS service
tts_service = None

class SpeakRequest(BaseModel):
    text: str

@app.on_event("startup")
async def startup_event():
    """Initialize the TTS service on startup."""
    global tts_service
    log.info("Starting TTS microservice...")
    try:
        tts_service = TTSService()
        tts_service.warmup()
        log.info("TTS microservice started and warmed up successfully")
    except Exception as e:
        log.error(f"Failed to start TTS microservice: {e}", exc_info=True)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    if tts_service:
        return {"status": "healthy"}
    else:
        return {"status": "unhealthy"}, 503

@app.post("/speak")
async def speak(request: SpeakRequest):
    """API endpoint to speak the given text."""
    if not tts_service:
        return {"error": "TTS service not initialized"}, 503
    try:
        tts_service.speak(request.text)
        return {"status": "success"}
    except Exception as e:
        log.error(f"Error during TTS speak request: {e}", exc_info=True)
        return {"error": str(e)}, 500

@app.post("/stream-speak")
async def stream_speak(request: SpeakRequest):
    """API endpoint to speak text using streaming mode."""
    if not tts_service:
        return {"error": "TTS service not initialized"}, 503
    try:
        # For now, we'll handle streaming at the service level
        # In a more advanced implementation, you could accept chunks via WebSocket
        tts_service.speak(request.text)
        return {"status": "streaming completed"}
    except Exception as e:
        log.error(f"Error during TTS streaming speak request: {e}", exc_info=True)
        return {"error": str(e)}, 500

@app.post("/warmup")
async def warmup():
    """API endpoint to warm up the TTS service."""
    if not tts_service:
        return {"error": "TTS service not initialized"}, 503
    try:
        tts_service.warmup()
        return {"status": "warmed up"}
    except Exception as e:
        log.error(f"Error during TTS warmup request: {e}", exc_info=True)
        return {"error": str(e)}, 500

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)


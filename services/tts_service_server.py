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
from typing import List
from services.tts_service import TTSService
from services.logger import app_logger

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

class StreamSpeakRequest(BaseModel):
    text_chunks: List[str]
    
@app.post("/stream-speak")
async def stream_speak(request: StreamSpeakRequest):
    """API endpoint to speak text chunks using streaming mode."""
    if not tts_service:
        return {"error": "TTS service not initialized"}, 503
    try:
        # Use the streaming interface with pre-chunked text
        tts_service.speak(chunks=request.text_chunks)
        return {"status": "streaming completed", "chunks_processed": len(request.text_chunks)}
    except Exception as e:
        log.error(f"Error during TTS streaming speak request: {e}", exc_info=True)
        return {"error": str(e)}, 500

@app.post("/speak-chunk")
async def speak_chunk(request: SpeakRequest):
    """API endpoint to speak a single text chunk immediately."""
    if not tts_service:
        return {"error": "TTS service not initialized"}, 503
    try:
        # Break text into smaller chunks for immediate processing
        chunks = tts_service._segment_text(request.text, max_chars=150)
        tts_service.speak(chunks=chunks)
        return {"status": "chunk completed", "chunks_generated": len(chunks)}
    except Exception as e:
        log.error(f"Error during TTS chunk speak request: {e}", exc_info=True)
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
    # Configure uvicorn logging to reduce HTTP request noise
    import logging
    
    # Set uvicorn access log level to WARNING to hide successful requests
    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    uvicorn_access_logger.setLevel(logging.WARNING)
    
    # Run server with reduced logging
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8001,
        log_level="info",  # Keep general uvicorn logs at info
        access_log=False   # Disable access logging completely
    )


#!/usr/bin/env python3
"""
STT microservice that provides speech-to-text functionality via an HTTP API.
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
import numpy as np
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from services.stt_service import STTService
from services.logger import app_logger

# Restore stderr and stdout after imports
os.dup2(original_stderr, 2)
os.dup2(original_stdout, 1)
os.close(original_stderr)
os.close(original_stdout)

# Initialize FastAPI app
app = FastAPI()
log = app_logger.get_logger("stt_microservice")

# Initialize STT service
stt_service = None

@app.on_event("startup")
async def startup_event():
    """Initialize the STT service on startup."""
    global stt_service
    log.info("Starting STT microservice...")
    try:
        # Note: DynamicRMS is not available in this isolated service.
        # The main process will handle VAD and silence detection.
        stt_service = STTService(dynamic_rms=None)
        log.info("STT microservice started and model loaded successfully")
    except Exception as e:
        log.error(f"Failed to start STT microservice: {e}", exc_info=True)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    if stt_service:
        return {"status": "healthy"}
    else:
        return {"status": "unhealthy"}, 503

@app.post("/transcribe")
async def transcribe(audio: UploadFile = File(...)):
    """API endpoint to transcribe the given audio data."""
    if not stt_service:
        return {"error": "STT service not initialized"}, 503
    try:
        audio_data = await audio.read()
        transcription = stt_service.transcribe_audio_bytes(audio_data)
        return {"transcription": transcription}
    except Exception as e:
        log.error(f"Error during STT transcribe request: {e}", exc_info=True)
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
        port=8002,
        log_level="info",  # Keep general uvicorn logs at info
        access_log=False   # Disable access logging completely
    )


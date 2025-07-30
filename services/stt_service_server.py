#!/usr/bin/env python3
"""
STT microservice that provides speech-to-text functionality via an HTTP API.
"""

import uvicorn
import numpy as np
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from .stt_service import STTService
from .logger import app_logger

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
    uvicorn.run(app, host="0.0.0.0", port=8002)


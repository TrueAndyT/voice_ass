#!/usr/bin/env python3
"""
TTS microservice that provides text-to-speech functionality via an HTTP API.
"""

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from .tts_service import TTSService
from .logger import app_logger

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


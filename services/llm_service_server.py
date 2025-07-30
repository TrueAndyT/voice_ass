#!/usr/bin/env python3
"""
LLM microservice that provides language model functionality via an HTTP API.
"""

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from .llm_service import LLMService
from .logger import app_logger

# Initialize FastAPI app
app = FastAPI()
log = app_logger.get_logger("llm_microservice")

# Initialize LLM service
llm_service = None

class ChatRequest(BaseModel):
    prompt: str

class WarmupResponse(BaseModel):
    status: str

@app.on_event("startup")
async def startup_event():
    """Initialize the LLM service on startup."""
    global llm_service
    log.info("Starting LLM microservice...")
    try:
        llm_service = LLMService(model='llama3.1:8b-instruct-q4_K_M')
        log.info("LLM microservice started successfully")
    except Exception as e:
        log.error(f"Failed to start LLM microservice: {e}", exc_info=True)

@app.post("/chat")
async def chat(request: ChatRequest):
    """API endpoint to get a response from the LLM."""
    if not llm_service:
        return {"error": "LLM service not initialized"}, 503
    try:
        response = llm_service.get_response(request.prompt)
        return {"response": response}
    except Exception as e:
        log.error(f"Error during LLM chat request: {e}", exc_info=True)
        return {"error": str(e)}, 500

@app.post("/warmup")
async def warmup():
    """API endpoint to warm up the LLM service."""
    if not llm_service:
        return {"error": "LLM service not initialized"}, 503
    try:
        llm_service.warmup_llm()
        return {"status": "warmed up"}
    except Exception as e:
        log.error(f"Error during LLM warmup request: {e}", exc_info=True)
        return {"error": str(e)}, 500

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)

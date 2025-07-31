#!/usr/bin/env python3
"""
LLM microservice that provides language model functionality via an HTTP API.
"""

import sys
import os
# Insert project root at the BEGINNING of path to avoid conflicts with installed packages
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from services.llm_service import LLMService
from services.logger import app_logger

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

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    if llm_service:
        return {"status": "healthy"}
    else:
        return {"status": "unhealthy"}, 503

@app.post("/chat")
async def chat(request: ChatRequest):
    """API endpoint to get a response from the LLM."""
    if not llm_service:
        return {"error": "LLM service not initialized"}, 503
    try:
        result = llm_service.get_response(request.prompt)
        
        # Handle both tuple and single return values
        if isinstance(result, tuple):
            response, metrics = result
        else:
            response = result
            metrics = {}
        
        return {"response": response, "metrics": metrics}
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
    # Configure uvicorn logging to reduce HTTP request noise
    import logging
    
    # Set uvicorn access log level to WARNING to hide successful requests
    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    uvicorn_access_logger.setLevel(logging.WARNING)
    
    # Run server with reduced logging
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8003,
        log_level="info",  # Keep general uvicorn logs at info
        access_log=False   # Disable access logging completely
    )

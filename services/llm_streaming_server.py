#!/usr/bin/env python3
"""
Enhanced LLM microservice with streaming capabilities using Server-Sent Events (SSE).
This allows real-time token streaming for TTS integration.
"""

import sys
import os
import json
import asyncio
from typing import AsyncGenerator

# Insert project root at the BEGINNING of path to avoid conflicts with installed packages
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import uvicorn
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import ollama
from services.llm_service import LLMService
from services.utils.logger import app_logger

# Initialize FastAPI app
app = FastAPI()
log = app_logger.get_logger("llm_streaming_microservice")

# Initialize LLM service
llm_service = None

class ChatRequest(BaseModel):
    prompt: str
    stream: bool = False
    chunk_threshold: int = 50  # Minimum characters before yielding chunk

class StreamingChatRequest(BaseModel):
    prompt: str
    chunk_threshold: int = 50
    sentence_boundary: bool = True  # Whether to break on sentence boundaries

@app.on_event("startup")
async def startup_event():
    """Initialize the LLM service on startup."""
    global llm_service
    log.info("Starting streaming LLM microservice...")
    try:
        llm_service = LLMService(model='llama3:8b-q4')
        log.info("Streaming LLM microservice started successfully")
    except Exception as e:
        log.error(f"Failed to start streaming LLM microservice: {e}", exc_info=True)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    if llm_service:
        return {"status": "healthy", "streaming": True}
    else:
        return {"status": "unhealthy"}, 503

@app.post("/chat")
async def chat(request: ChatRequest):
    """API endpoint to get a response from the LLM (non-streaming)."""
    if not llm_service:
        return {"error": "LLM service not initialized"}, 503
    
    try:
        if request.stream:
            # Redirect to streaming endpoint
            return {"error": "Use /chat/stream for streaming responses"}, 400
        
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

@app.post("/chat/stream")
async def chat_stream(request: StreamingChatRequest):
    """API endpoint for streaming LLM responses using Server-Sent Events."""
    if not llm_service:
        return {"error": "LLM service not initialized"}, 503
    
    async def generate_stream() -> AsyncGenerator[str, None]:
        """Generate streaming response chunks."""
        try:
            log.info(f"Starting streaming response for: '{request.prompt[:50]}...'")
            
            # Detect intent first
            intent = llm_service.intent_detector.detect(request.prompt)
            log.info(f"Detected intent: {intent}")
            
            # Send intent info
            yield f"data: {json.dumps({'type': 'intent', 'content': intent})}\n\n"
            
            # Handle specialized intents (non-streaming for now)
            if intent in llm_service.handlers:
                reply = llm_service.handlers[intent].handle(request.prompt)
                yield f"data: {json.dumps({'type': 'complete', 'content': reply, 'is_final': True})}\n\n"
                return
            
            # Prepare messages for streaming
            llm_service.history.append({'role': 'user', 'content': request.prompt})
            messages_to_send = llm_service.history[-16:]
            if messages_to_send[0]['role'] != 'system':
                messages_to_send = [llm_service.system_prompt] + messages_to_send
            
            # Start streaming from Ollama
            import time
            start_time = time.time()
            first_token_time = None
            full_response = ""
            chunk_buffer = ""
            
            # Use asyncio to run blocking ollama.chat in executor
            def get_ollama_stream():
                return ollama.chat(
                    model=llm_service.model,
                    messages=messages_to_send,
                    stream=True
                )
            
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            stream = await loop.run_in_executor(None, get_ollama_stream)
            
            for chunk in stream:
                if 'message' in chunk and 'content' in chunk['message']:
                    content = chunk['message']['content']
                    if content:
                        if first_token_time is None:
                            first_token_time = time.time()
                            # Send first token timing
                            ttft = first_token_time - start_time
                            yield f"data: {json.dumps({'type': 'first_token', 'time': ttft})}\n\n"
                        
                        full_response += content
                        chunk_buffer += content
                        
                        # Check if we should yield this chunk
                        should_yield = (
                            len(chunk_buffer) >= request.chunk_threshold or
                            (request.sentence_boundary and _is_sentence_boundary(chunk_buffer))
                        )
                        
                        if should_yield:
                            chunk_data = {
                                'type': 'chunk',
                                'content': chunk_buffer,
                                'is_final': False,
                                'elapsed_time': time.time() - start_time
                            }
                            yield f"data: {json.dumps(chunk_data)}\n\n"
                            chunk_buffer = ""
                            
                            # Small delay to prevent overwhelming the client
                            await asyncio.sleep(0.01)
            
            # Send any remaining content
            if chunk_buffer:
                chunk_data = {
                    'type': 'chunk',
                    'content': chunk_buffer,
                    'is_final': False
                }
                yield f"data: {json.dumps(chunk_data)}\n\n"
            
            # Add to history
            llm_service.history.append({'role': 'assistant', 'content': full_response})
            llm_service._append_to_dialog_log("ASSISTANT", full_response)
            
            # Send completion with metrics
            total_duration = time.time() - start_time
            final_metrics = {
                'total_duration': total_duration,
                'time_to_first_token': first_token_time - start_time if first_token_time else 0,
                'total_length': len(full_response),
                'estimated_tokens': len(full_response.split()),
                'tokens_per_second': len(full_response.split()) / total_duration if total_duration > 0 else 0
            }
            
            completion_data = {
                'type': 'complete',
                'content': full_response,
                'metrics': final_metrics,
                'is_final': True
            }
            yield f"data: {json.dumps(completion_data)}\n\n"
            
        except Exception as e:
            error_data = {
                'type': 'error',
                'content': str(e),
                'is_final': True
            }
            yield f"data: {json.dumps(error_data)}\n\n"
            log.error(f"Error in streaming response: {e}", exc_info=True)
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )

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

def _is_sentence_boundary(text: str) -> bool:
    """Check if text ends with a sentence boundary."""
    import re
    return bool(re.search(r'[.!?]\s*$', text.strip()))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)

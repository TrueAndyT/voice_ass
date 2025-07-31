# API Endpoints Reference

This document lists all HTTP endpoints across all microservices to ensure consistent API design and prevent endpoint conflicts.

## Service Overview

| Service | Port | Server File | Purpose |
|---------|------|-------------|---------|
| **TTS Service** | 8001 | `tts_service_server.py` | Text-to-Speech synthesis |
| **STT Service** | 8002 | `stt_service_server.py` | Speech-to-Text transcription |
| **LLM Service** | 8003 | `llm_streaming_server.py` | Language model with streaming |

---

## TTS Service Endpoints (Port 8001)

### Base URL: `http://127.0.0.1:8001`

| Endpoint | Method | Request Body | Response | Description | Status |
|----------|--------|-------------|----------|-------------|---------|
| `/health` | GET | - | `{"status": "healthy"}` | Health check | ✅ Active |
| `/speak` | POST | `{"text": str}` | `{"status": "success"}` | **ONLY USED ENDPOINT** | ✅ Active |
| `/warmup` | POST | - | `{"status": "warmed up"}` | Warm up TTS pipeline | ✅ Active |

### Request Models
```python
class SpeakRequest(BaseModel):
    text: str

class StreamSpeakRequest(BaseModel):
    text_chunks: List[str]
```

---

## STT Service Endpoints (Port 8002)

### Base URL: `http://127.0.0.1:8002`

| Endpoint | Method | Request Body | Response | Description | Status |
|----------|--------|-------------|----------|-------------|---------|
| `/health` | GET | - | `{"status": "healthy"}` | Health check | ✅ Active |
| `/transcribe` | POST | `audio: UploadFile` | `{"transcription": str}` | Audio transcription | ✅ Active |

### Request Format
- **Content-Type**: `multipart/form-data`
- **Field**: `audio` (binary audio file)

---

## LLM Service Endpoints (Port 8003)

### Base URL: `http://127.0.0.1:8003`

| Endpoint | Method | Request Body | Response | Description | Status |
|----------|--------|-------------|----------|-------------|---------|
| `/health` | GET | - | `{"status": "healthy", "streaming": true}` | Health check | ✅ Active |
| `/chat` | POST | `{"prompt": str}` | `{"response": str, "metrics": dict}` | Standard LLM chat | ✅ Active |
| `/chat/stream` | POST | `{"prompt": str, "chunk_threshold": int, "sentence_boundary": bool}` | **SSE Stream** | **KEY** Streaming LLM chat | ✅ Active |
| `/warmup` | POST | - | `{"status": "warmed up"}` | Warm up LLM model | ✅ Active |

### Request Models
```python
class ChatRequest(BaseModel):
    prompt: str
    stream: bool = False
    chunk_threshold: int = 50

class StreamingChatRequest(BaseModel):
    prompt: str
    chunk_threshold: int = 50
    sentence_boundary: bool = True
```

### SSE Stream Format
**Content-Type**: `text/event-stream`

```
data: {"type": "intent", "content": "general"}

data: {"type": "first_token", "time": 0.123}

data: {"type": "chunk", "content": "Hello there", "is_final": false}

data: {"type": "complete", "content": "Full response", "metrics": {...}, "is_final": true}
```

---

## Client Usage Patterns

### TTS Clients

#### Standard TTS Client
```python
# services/tts_client.py
tts_client.speak("Hello world")          # → POST /speak
tts_client.warmup()                      # → POST /warmup
tts_client.health_check()                # → GET /health
```

#### Streaming TTS Client
```python
# services/tts_streaming_client.py
tts_client.speak("Hello world")          # → POST /speak
tts_client._speak_chunk("Hello")         # → POST /speak-chunk (with fallback)
tts_client.stream_speak(text_iterator)   # → Multiple /speak-chunk calls
tts_client.warmup()                      # → POST /warmup
tts_client.health_check()                # → GET /health
```

### STT Clients

```python
# services/stt_client.py
stt_client.transcribe_audio_bytes(data)  # → POST /transcribe
stt_client.health_check()                # → GET /health
```

### LLM Clients

#### Standard LLM Client
```python
# services/llm_client.py
llm_client.get_response("Hello")         # → POST /chat
llm_client.get_response_stream("Hello")  # → POST /chat/stream (SSE)
llm_client.warmup_llm()                  # → POST /warmup
llm_client.health_check()                # → GET /health
```

#### Streaming LLM Client
```python
# services/llm_streaming_client.py
llm_client.get_response("Hello")                    # → POST /chat
llm_client.get_streaming_response("Hello")          # → POST /chat/stream (SSE)
llm_client.get_streaming_text("Hello")              # → POST /chat/stream (text only)
llm_client.warmup_llm()                             # → POST /warmup
llm_client.health_check()                           # → GET /health
```

---

## Error Handling Patterns

### Standard Error Response
```json
{
  "error": "Service not initialized",
  "status_code": 503
}
```

### HTTP Status Codes

| Code | Usage | Description |
|------|-------|-------------|
| **200** | Success | Request completed successfully |
| **404** | Not Found | Endpoint doesn't exist (triggers fallback) |
| **500** | Server Error | Internal service error |
| **503** | Service Unavailable | Service not initialized |

---

## Endpoint Consistency Rules

### 1. **Health Check Pattern**
- **Endpoint**: `GET /health`
- **Response**: `{"status": "healthy"}` or `{"status": "unhealthy"}`
- **Usage**: All clients use this for service readiness checks

### 2. **Warmup Pattern**
- **Endpoint**: `POST /warmup`
- **Response**: `{"status": "warmed up"}`
- **Usage**: Initialize models for optimal performance

### 3. **Error Response Pattern**
- **Format**: `{"error": "description"}`
- **HTTP Codes**: 500 for service errors, 503 for unavailable

### 4. **Request Model Naming**
- **Pattern**: `{Action}Request` (e.g., `SpeakRequest`, `ChatRequest`)
- **Content**: Single purpose, clear field names

---

## Current Issues & Fixes Needed

### ⚠️ **TTS Server Needs Restart**
**Problem**: New endpoints `/speak-chunk` and `/stream-speak` added but server not restarted
**Solution**: Restart TTS microservice to pick up new endpoints

### ⚠️ **Typing Compatibility**
**Problem**: Used `list[str]` instead of `List[str]` (Python 3.9+ syntax)
**Status**: ✅ Fixed with `from typing import List`

### ✅ **Fallback Strategy** 
**Problem**: Clients fail when new endpoints don't exist
**Status**: ✅ **IMPLEMENTED** in `tts_streaming_client.py`

**Solution**: Endpoint fallbacks implemented:

```python
def _speak_chunk(self, text: str):
    try:
        # Try optimized endpoint
        response = requests.post(f"{self.base_url}/speak-chunk", ...)
        if response.status_code == 404:
            # Fallback to standard endpoint
            self.log.debug("speak-chunk not available, falling back")
            return self.speak(text)
    except RequestException as e:
        # Network fallback
        self.log.debug(f"Endpoint failed ({e}), trying fallback")
        return self.speak(text)
```

---

## Integration Flow Mapping

### **Main Streaming Flow**
```
User Input
    ↓
STT: POST /transcribe
    ↓
LLM: POST /chat/stream (SSE)
    ↓
TTS: POST /speak-chunk (chunked)
    ↓
Audio Output
```

### **Fallback Flow**
```
User Input
    ↓
STT: POST /transcribe
    ↓
LLM: POST /chat (if streaming fails)
    ↓
TTS: POST /speak (if chunking fails)
    ↓
Audio Output
```

---

## Testing Endpoints

### Quick Health Check
```bash
curl http://127.0.0.1:8001/health  # TTS
curl http://127.0.0.1:8002/health  # STT  
curl http://127.0.0.1:8003/health  # LLM
```

### Test New TTS Endpoints
```bash
# Standard speak
curl -X POST http://127.0.0.1:8001/speak \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world"}'

# Chunked speak (if available)
curl -X POST http://127.0.0.1:8001/speak-chunk \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world"}'
```

### Test LLM Streaming
```bash
# SSE streaming
curl -X POST http://127.0.0.1:8003/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello", "chunk_threshold": 50}' \
  --no-buffer
```

---

## Deployment Checklist

- [ ] **TTS Server**: Restart to enable `/speak-chunk` and `/stream-speak`
- [ ] **LLM Server**: Verify streaming server is running (not basic server)
- [ ] **Health Checks**: All services respond to `/health`
- [ ] **Fallbacks**: Client fallback logic works for missing endpoints
- [ ] **Logging**: HTTP access logs suppressed (debug only)
- [ ] **Performance**: All services warmed up via `/warmup`

This endpoints reference ensures all microservices have consistent APIs and proper fallback strategies for robust operation.

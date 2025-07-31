# Service Methods Reference

This document lists all methods across LLM and TTS services to ensure consistent interfaces and prevent naming conflicts.

## LLM Services

### 1. LLMService (services/llm_service.py)
**Purpose**: Local LLM service using Ollama directly

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `__init__` | `model='mistral'` | - | Initialize service with model name |
| `get_response` | `prompt: str` | `tuple(str, dict)` | Get complete response with metrics |
| `get_response_stream` | `prompt: str` | `Iterator[dict]` | **NEW** Stream response as chunks (simulated) |
| `warmup_llm` | - | - | Warm up model for faster responses |
| `_check_gpu_availability` | - | - | Check and log GPU status |
| `_build_system_prompt` | - | `str` | Build system prompt with memory |
| `_load_memory` | - | `str` | Load long-term memories |
| `_load_personality` | - | `str` | Load personality from config |
| `_create_new_dialog_log` | - | - | Create session dialog log |
| `_append_to_dialog_log` | `role: str, text: str` | - | Append to dialog log |
| `_extract_ollama_metrics` | `response: dict` | `dict` | Extract performance metrics |

### 2. LLMClient (services/llm_client.py)
**Purpose**: HTTP client for LLM microservice

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `__init__` | `host, port, timeout=120` | - | Initialize HTTP client |
| `get_response` | `prompt: str` | `tuple(str, dict)` | Get complete response via HTTP |
| `get_response_stream` | `prompt: str` | `Iterator[dict]` | **NEW** Stream response via SSE |
| `warmup_llm` | - | `dict` | Warm up via HTTP |
| `health_check` | - | `bool` | Check service health |

### 3. StreamingLLMClient (services/llm_streaming_client.py)
**Purpose**: Enhanced streaming LLM client with SSE support

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `__init__` | `host, port, timeout=120` | - | Initialize streaming client |
| `get_response` | `prompt: str` | `tuple(str, dict)` | Non-streaming response (compatibility) |
| `get_streaming_response` | `prompt, chunk_threshold=50, sentence_boundary=True` | `Iterator[dict]` | Full streaming with control |
| `get_streaming_text` | `prompt: str, **kwargs` | `Iterator[str]` | Simple text-only streaming |
| `warmup_llm` | - | `dict` | Warm up service |
| `health_check` | - | `bool` | Check service health |

## TTS Services

### 4. TTSService (services/tts_service.py)
**Purpose**: Core TTS service using Kokoro with GPU acceleration

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `__init__` | `voice_model='af_heart'` | - | Initialize with voice model |
| `speak` | `text=None, chunks=None` | - | **UPDATED** Speak text or pre-chunked text |
| `stream_speak` | `chunk_iterator: Iterator[str]` | - | Speak from streaming chunks |
| `warmup` | - | - | Warm up TTS pipeline |
| `stop` | - | - | Stop current playback |
| `_get_device` | - | `str` | Determine CUDA/CPU device |
| `_build_pipeline` | - | `KPipeline` | Build Kokoro pipeline |
| `_segment_text` | `text: str, max_chars=200` | `list[str]` | **UPDATED** Segment text into chunks |
| `_generate_chunk_audio` | `chunk: str` | `np.array` | **UPDATED** Generate audio with memory mgmt |

### 5. TTSStreamingClient (services/tts_streaming_client.py)
**Purpose**: HTTP client for TTS microservice with streaming support

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `__init__` | `host, port, timeout=30` | - | Initialize streaming client |
| `speak` | `text: str` | `dict` | Send text to TTS via HTTP |
| `stream_speak` | `text_stream: Iterator[str], chunk_size=100` | - | **UPDATED** Stream text chunks |
| `_speak_chunk` | `text: str` | `dict` | **NEW** Send single chunk via /speak-chunk |
| `stream_from_llm` | `llm_stream: Iterator[dict], text_key='content'` | - | Stream from LLM output |
| `warmup` | - | `dict` | Warm up TTS service |
| `health_check` | - | `bool` | Check service health |
| `_find_break_point` | `text: str` | `int` | Find optimal text break point |

### 6. LLMToTTSStreamingBridge (services/tts_streaming_client.py)
**Purpose**: Bridge connecting LLM streaming output to TTS input

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `__init__` | `tts_client: TTSStreamingClient` | - | Initialize bridge |
| `stream_llm_to_tts` | `llm_stream: Iterator[dict], chunk_size=100, text_key='content'` | - | **KEY METHOD** Bridge LLM → TTS |

## TTS Server Endpoints

### 7. TTS Service Server (services/tts_service_server.py)
**Purpose**: FastAPI server providing TTS HTTP endpoints

| Endpoint | Method | Request Body | Response | Description |
|----------|--------|--------------|----------|-------------|
| `/health` | GET | - | `{"status": "healthy"}` | Health check |
| `/speak` | POST | `{"text": str}` | `{"status": "success"}` | Standard TTS |
| `/speak-chunk` | POST | `{"text": str}` | `{"status": "chunk completed", "chunks_generated": int}` | **NEW** Chunked TTS |
| `/stream-speak` | POST | `{"text_chunks": list[str]}` | `{"status": "streaming completed", "chunks_processed": int}` | **NEW** Multi-chunk TTS |
| `/warmup` | POST | - | `{"status": "warmed up"}` | Warm up service |

## Factory Functions

### 8. Convenience Functions
**Purpose**: Easy service creation and configuration

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `create_streaming_tts_client` | `host, port` | `TTSStreamingClient` | Create configured TTS client |
| `create_llm_tts_bridge` | `tts_host, tts_port` | `LLMToTTSStreamingBridge` | **KEY FUNCTION** Create streaming bridge |
| `create_streaming_integration` | `host, port` | `tuple` | Create LLM client + integration |

## Method Naming Conventions

### **Consistent Patterns**
1. **Core Methods**: `get_response()`, `get_response_stream()`
2. **Streaming**: `stream_*()` for streaming operations
3. **Internal**: `_private_method()` with underscore prefix
4. **Health**: `health_check()`, `warmup()`/`warmup_llm()`
5. **HTTP**: Same names as service methods for consistency

### **Parameter Patterns**
1. **Text Input**: `text: str`, `prompt: str`
2. **Streaming**: `Iterator[str]` or `Iterator[dict]`
3. **Chunks**: `chunk_size: int`, `chunks: list[str]`
4. **Config**: `host: str`, `port: int`, `timeout: int`

### **Return Patterns**
1. **LLM Responses**: `tuple(str, dict)` for (response, metrics)
2. **Streaming**: `Iterator[dict]` with `{'type': ..., 'content': ...}`
3. **HTTP**: `dict` with status and data
4. **Health**: `bool` for simple checks

## Integration Flow

### **Main Streaming Flow**
```python
# 1. Create bridge
bridge = create_llm_tts_bridge()

# 2. Get LLM stream
llm_stream = llm_service.get_response_stream(prompt)

# 3. Stream to TTS
bridge.stream_llm_to_tts(llm_stream, chunk_size=80)
```

### **Fallback Flow**
```python
# 1. Try streaming
try:
    bridge.stream_llm_to_tts(llm_stream)
except Exception:
    # 2. Fall back to traditional
    response, metrics = llm_service.get_response(prompt)
    streaming_tts.speak(response)
```

## Key Improvements Made

1. **Memory Management**: Added `torch.no_grad()` wrappers in TTS generation
2. **Chunking**: Reduced chunk sizes (200 chars) for better streaming
3. **New Endpoints**: `/speak-chunk` for optimized single-chunk processing
4. **Streaming Bridge**: Direct LLM → TTS connection with buffering
5. **Consistent Interfaces**: All services have `get_response_stream()` method
6. **Error Handling**: Multiple fallback levels for robust operation
7. **Fixed Microservices**: Uses `llm_streaming_server` for proper `/chat/stream` support
8. **Proper Health Checks**: All clients use `/health` endpoint correctly

## Usage Examples

### **Basic Streaming**
```python
# LLM streaming
for chunk in llm_service.get_response_stream(prompt):
    if chunk['type'] == 'chunk':
        print(chunk['content'], end='')

# TTS streaming  
tts_client.stream_speak(text_chunks)
```

### **Integrated Streaming**
```python
# One-line integration
bridge = create_llm_tts_bridge()
bridge.stream_llm_to_tts(
    llm_service.get_response_stream(prompt),
    chunk_size=80
)
```

This reference document ensures all method names, parameters, and return types are consistent across the entire LLM → TTS streaming pipeline.

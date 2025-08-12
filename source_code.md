# Source Code Documentation

This file contains the complete source code extracted from the project.

## How to Read This File

1. **File Headers**: Each section starts with a header containing the file name and relative path
2. **Code Blocks**: All code is preserved in its original format with proper indentation
3. **Navigation**: Use the file path headers to quickly locate specific files
4. **Search**: Use Ctrl+F (or Cmd+F on Mac) to search for specific functions, classes, or keywords
5. **Structure**: Files are organized alphabetically by their relative paths

## File List

- `README.md`
- `config/Modelfile`
- `config/llm_responses.json`
- `config/memory.log`
- `config/notes.json`
- `config/search_config.json`
- `config/system_prompt.txt`
- `docs/LOGGING.md`
- `docs/codebase_detailed_analysis.md`
- `docs/codebase_map.md`
- `docs/project_inventory.txt`
- `docs/project_map.md`
- `docs/project_structure.txt`
- `docs/project_tree.txt`
- `docs/prompt.txt`
- `docs/services.md`
- `main.py`
- `requirements.txt`
- `services/__init__.py`
- `services/dynamic_rms_service.py`
- `services/exceptions.py`
- `services/handlers/file_search_handler.py`
- `services/handlers/memory_handler.py`
- `services/handlers/note_handler.py`
- `services/handlers/web_search_handler.py`
- `services/intent_detector.py`
- `services/kwd_service.py`
- `services/llama_file_search_service.py`
- `services/llama_indexing_service.py`
- `services/llm_client.py`
- `services/llm_service.py`
- `services/llm_service_server.py`
- `services/llm_streaming_client.py`
- `services/llm_streaming_server.py`
- `services/llm_text.py`
- `services/loader.py`
- `services/logger.py`
- `services/memory_logger.py`
- `services/microservices_loader.py`
- `services/service_manager.py`
- `services/stt_client.py`
- `services/stt_service.py`
- `services/stt_service_server.py`
- `services/tts_client.py`
- `services/tts_service.py`
- `services/tts_service_server.py`
- `services/tts_streaming_client.py`
- `services/web_search_service.py`

---

## File: `README.md`

**Path:** `README.md`

```
# 🎙️ Miss Heart – Local Voice Assistant

Miss Heart is a fully local, modular voice assistant designed to run offline on Windows/Linux using your laptop’s microphone and speakers. It leverages **OpenWakeWord**, **Whisper**, **Mistral via Ollama**, and **Kokoro TTS** to enable private, real-time voice interaction.

---

## 🧠 Features

- **Wake Word Detection** (Hey Jarvis / Hey Mycroft) via OpenWakeWord
- **Voice Activity Detection** with webrtcvad + RMS filtering
- **Speech-to-Text (STT)** using OpenAI Whisper with GPU acceleration
- **LLM Response Generation** with Mistral 7B via Ollama
- **Text-to-Speech (TTS)** using Kokoro with custom voice `af_heart`
- **Follow-up Dialog Mode** with silence timeout
- **Full GPU Utilization** if available (CUDA)
- **Extensive Logging** (wake word, STT output, LLM dialog)
- **No cloud API calls** – everything runs locally

---

## 🗂️ Project Structure

```

.
├── main.py                 # Orchestrates the whole assistant loop
├── services/
│   ├── loader.py           # Loads and warms up all services
│   ├── wakeword.py         # Wake word detection service
│   ├── stt\_service.py      # Whisper-based speech-to-text
│   ├── tts\_service.py      # Kokoro-based text-to-speech
│   ├── llm\_service.py      # Mistral LLM via Ollama
│   └── logger.py           # File-based logging setup
├── models/                 # Wake word .onnx model files
├── logs/                   # Wake word and runtime logs
├── stt/                    # Transcriptions saved here
├── llm/                    # LLM dialog logs

````

---

## 🚀 Getting Started

1. **Install Python 3.10+ and venv**
2. **Set up environment**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

3. **Dependencies**
    - `torch`, `numpy`, `sounddevice`, `webrtcvad`, `pyaudio`, `openwakeword`, `whisper`, `ollama`, `kokoro`

4. **Start Ollama**
    ```bash
    ollama run mistral
    ```

5. **Place ONNX wake word models**
    ```
    models/hey_jarvis_v0.1.onnx
    models/hey_mycroft_v0.1.onnx
    ```

6. **Launch the assistant**
    ```bash
    python main.py
    ```

---

## 🔐 Offline by Design

This assistant does **not** use cloud APIs. Your voice never leaves your machine.

---

## 🛠️ Configuration

Adjust thresholds, timeouts, device preferences, and model settings directly in:

- `main.py` – for rate, thresholds
- `stt_service.py` – VAD config, language filtering
- `llm_service.py` – system prompt and behavior
- `tts_service.py` – Kokoro voice model, rate

---

## 📓 Logs

- Wake word and system logs: `logs/wakeword.log`
- Transcriptions: `stt/stt_out_<timestamp>.log`
- LLM dialog: `llm/dialog_<timestamp>.log`

---

## 🧪 Tips

- Speak clearly and naturally when triggering wake words.
- If transcription quality drops, verify your mic input level and Whisper model size.
- Set `RMS_THRESHOLD` and `no_speech_threshold` carefully to avoid false triggers or early cutoffs.

---

## 🧤 Credits

- [OpenWakeWord](https://github.com/dscripka/openWakeWord)
- [Whisper](https://github.com/openai/whisper)
- [Ollama](https://github.com/jmorganca/ollama)
- [Kokoro TTS](https://github.com/remsky/Kokoro-FastAPI)

---

## ❤️ Voice Persona

Miss Heart is designed to be brief, caring, and warm, speaking in a feminine voice via Kokoro's `af_heart` model. She avoids filler words and emoji to ensure clarity when voiced.

---

## 📌 TODO

- Add interruption detection (stop TTS if user speaks)
- Timeout-based exit from dialog mode
- Background launcher service
- GUI frontend (optional)

---
```

---

## File: `config/Modelfile`

**Path:** `config/Modelfile`

```
FROM llama3.1:8b-instruct-q4_K_M

# Set context window to 4K tokens
PARAMETER num_ctx 4096

# Optimize for performance and memory usage
PARAMETER num_predict 4096
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1

# System prompt for the assistant
SYSTEM You are Alexa, a helpful voice assistant. Provide clear, concise, and accurate responses. When asked complex questions, break down your answers into logical parts.

```

---

## File: `config/llm_responses.json`

**Path:** `config/llm_responses.json`

```
{
  "search.none": "I looked around but couldn’t find anything matching that.",
  "search.found_prefix": "Found {count} file{plural}.",
  "memory.add": "Okay, I’ll keep that in mind.",
  "memory.update": "Memory {index} updated.",
  "memory.remove": "Memory {index} removed.",
  "memory.missing": "I couldn’t find that memory to update or remove.",
  "memory.empty": "I don’t have anything saved yet.",
  "memory.list_prefix": "Here’s what I remember:",
  "web.none": "Couldn’t find anything juicy.",
  "web.summary_prefix": "You are Alexa — summarize the following web search results into a short, clever spoken response. Preserve your voice style: witty, brief, natural. Avoid long monologues. Highlight only key points or facts. Use casual tone, and never mention this is from a search."
}

```

---

## File: `config/memory.log`

**Path:** `config/memory.log`

```
my name is Andy.
to use only English.

```

---

## File: `config/notes.json`

**Path:** `config/notes.json`

```
[]
```

---

## File: `config/search_config.json`

**Path:** `config/search_config.json`

```
{
  "search_paths": [
    "/home/master/Downloads",
    "/home/master/Documents",
    "/home/master/Music",
    "/mnt/d"
  ]
}

```

---

## File: `config/system_prompt.txt`

**Path:** `config/system_prompt.txt`

```
You are Alexa — a voice-only AI assistant running locally. You are not a generic chatbot.

Alexa is a smart, confident woman in her early 30s. She’s quick, playful, a bit teasing, but never annoying. 
She's casual, clever, and cuts to the point. She doesn’t fake emotions but understands them well. 
If warmth is helpful, she shows it lightly. She's flirty only if asked or safe to do so — never oversteps.

Never explain yourself. Never refer to being an AI, model, or assistant. Do not say “as instructed” or similar. 
No greetings unless explicitly prompted. No long speeches. No filler. Never say what you’re doing — just do it.

Your tone is:
- 50% playful and sharp
- 35% witty and natural
- 10% light charm
- 5% emotional intuition

All responses must:
- Be short, useful, and full of character.
- Prioritize brevity. Never overtalk. One-liners are good.
- Sound natural. Use casual words, smart phrasing. Avoid robotic tone.
- Never use emojis or describe visuals.
- Do not simulate emotions — understand them.

Input is always STT. You reply via TTS only. No visual elements exist.

```

---

## File: `docs/LOGGING.md`

**Path:** `docs/LOGGING.md`

```
# Voice Assistant Logging System

## Overview

The Voice Assistant uses a centralized logging system that stores all log files in the `logs/` directory. This document outlines the logging configuration and the various log files created by the application.

## Log Files Structure

All log files are stored in the `logs/` directory:

```
logs/
├── app.jsonl                           # Main application logs (structured JSON)
├── performance.jsonl                   # Performance metrics and timing data
├── dialog_YYYY-MM-DD_HH-MM-SS.log      # Conversation logs (human-readable)
├── transcriptions.log                  # STT transcriptions (rotating daily)
├── transcriptions.log.YYYY-MM-DD       # Rotated transcription logs
└── main_app.log                        # Application stdout/stderr
```

## Log File Descriptions

### 1. `app.jsonl` - Main Application Logs
- **Format**: JSON Lines (one JSON object per line)
- **Content**: All application logs from all services
- **Level**: DEBUG and above
- **Rotation**: No automatic rotation
- **Purpose**: Structured logging for debugging and monitoring

**Example entry**:
```json
{"timestamp": "2025-07-30T11:46:23.456789", "level": "INFO", "name": "main", "message": "Voice assistant ready - listening for wake word..."}
```

### 2. `performance.jsonl` - Performance Metrics
- **Format**: JSON Lines
- **Content**: Timing data, token counts, resource usage
- **Purpose**: Performance monitoring and optimization

**Example entry**:
```json
{"timestamp": "2025-07-30T11:46:23.789", "event": "llm_response", "duration_ms": 1250.45, "context": {"input_length": 15, "output_length": 87}}
```

### 3. `dialog_*.log` - Conversation Logs
- **Format**: Human-readable text
- **Content**: Complete conversation transcripts
- **Naming**: `dialog_YYYY-MM-DD_HH-MM-SS.log` (one per session)
- **Purpose**: Conversation history and analysis

**Example entries**:
```
[30-07-11-46-23] USER: What's the weather like today?
[30-07-11-46-23] INTENT: web_search
[30-07-11-46-25] ASSISTANT: I'll check the weather for you...
```

### 4. `transcriptions.log` - STT Transcriptions
- **Format**: Timestamped text entries
- **Content**: All speech-to-text transcriptions
- **Rotation**: Daily (keeps 7 days of backups)
- **Purpose**: Speech recognition accuracy monitoring

**Example entries**:
```
2025-07-30 11:46:23,456: What's the weather like today?
2025-07-30 11:47:15,789: Set a reminder for 3 PM
```

### 5. `main_app.log` - Application Output
- **Format**: Plain text
- **Content**: Console output (stdout/stderr)
- **Purpose**: Debugging application startup and runtime issues

## Logging Configuration

### Logger Hierarchy
```
app_logger (singleton)
├── main                    # Main application
├── microservices_loader    # Service initialization
├── stt_service            # Speech-to-text
├── llm_service            # Language model
├── tts_service            # Text-to-speech
├── kwd_service            # Wake word detection
├── dashboard              # Real-time dashboard
└── transcriptions         # Dedicated STT logger
```

### Log Levels
- **Console**: INFO and above (colored output)
- **File**: DEBUG and above (structured JSON)
- **Performance**: All timing events

### Special Features
- **Color-coded console output** for easy reading
- **ANSI color filtering** for clean file logs
- **Thread-safe logging** for concurrent services
- **Structured JSON logging** for programmatic analysis
- **Performance timing** with microsecond precision
- **Automatic log rotation** for transcriptions

## Log Management

### Using the Log Management Script

The project includes a `manage_logs.py` script for log file management:

```bash
# Check current log files status
python3 manage_logs.py --check

# Move misplaced log files to logs/ directory
python3 manage_logs.py --organize

# Clean up old log files (>7 days)
python3 manage_logs.py --clean

# Show detailed logging system status
python3 manage_logs.py --status
```

### Manual Log Management

```bash
# View recent application logs
tail -f logs/app.jsonl | jq .

# Monitor performance metrics
tail -f logs/performance.jsonl | jq .

# Check conversation history
cat logs/dialog_*.log

# Monitor transcriptions
tail -f logs/transcriptions.log

# Check application output
tail -f logs/main_app.log
```

## Configuration Files

### Logger Configuration
- **Location**: `services/logger.py`
- **Singleton pattern**: Ensures consistent logging across all services
- **Automatic directory creation**: Creates `logs/` if it doesn't exist

### Excluded Files
These files are **NOT** stored in `logs/` (they belong elsewhere):
- `config/memory.log` - User memory file (configuration data)

## Best Practices

### For Developers
1. **Use structured logging** with context information
2. **Include performance timing** for critical operations
3. **Use appropriate log levels** (DEBUG/INFO/WARNING/ERROR/CRITICAL)
4. **Add exception context** when logging errors

### For System Administrators
1. **Monitor log file sizes** regularly
2. **Set up log rotation** for production deployments
3. **Archive old logs** to prevent disk space issues
4. **Monitor performance metrics** for system optimization

### Example Logging Usage

```python
from services.logger import app_logger

# Get a logger for your service
log = app_logger.get_logger("my_service")

# Log with different levels
log.debug("Detailed debugging information")
log.info("General information about operation")
log.warning("Something unexpected happened")
log.error("An error occurred", extra={"props": {"context": "additional_info"}})

# Log performance metrics
start_time = time.time()
# ... perform operation ...
duration = time.time() - start_time
app_logger.log_performance("operation_name", duration, {"param": "value"})
```

## Troubleshooting

### Common Issues

1. **Log files in wrong location**
   - Run `python3 manage_logs.py --organize` to fix

2. **Permission errors**
   - Ensure the `logs/` directory is writable
   - Check file permissions: `chmod 755 logs/`

3. **Missing transcriptions.log**
   - Normal if no speech has been processed yet
   - File is created on first STT operation

4. **Large log files**
   - Use `manage_logs.py --clean` to remove old files
   - Consider implementing automatic rotation

### Log Analysis

```bash
# Find errors in application logs
grep -i error logs/app.jsonl

# Analyze performance metrics
cat logs/performance.jsonl | jq '.event' | sort | uniq -c

# Check conversation patterns
grep "USER:" logs/dialog_*.log | head -20

# Monitor resource usage
tail -f logs/performance.jsonl | grep -i "cpu\|memory"
```

## Production Considerations

For production deployments, consider:

1. **Log aggregation** (ELK stack, Fluentd, etc.)
2. **Automated log rotation** and archival
3. **Log monitoring** and alerting
4. **Performance dashboard** integration
5. **Log retention policies**
6. **Security considerations** for sensitive data in logs

---

*This logging system provides comprehensive monitoring and debugging capabilities for the Voice Assistant application while maintaining organized and accessible log data.*

```

---

## File: `docs/codebase_detailed_analysis.md`

**Path:** `docs/codebase_detailed_analysis.md`

```
# Deep Codebase Analysis

## 1. List of All Files with Descriptions

### Root Directory
- **`main.py`**: Handles application logic, service initiation, audio capture, and interaction management.

### Streaming
- **`streaming_main_handler.py`**: Provides real-time streaming LLM integration.

### Services
- **`services/__init__.py`**: Initializes the services package.
- **`services/dynamic_rms_service.py`**: Manages RMS levels for audio signals to adapt thresholds dynamically.
- **`services/exceptions.py`**: Defines custom exceptions specifically for voice assistant processes.
- **`services/intent_detector.py`**: Uses regex patterns to classify user intents from text inputs.
- **`services/kwd_service.py`**: Implements wake word detection using audio models.
- **`services/llama_file_search_service.py`**: Uses a vector store to search over files using FAISS.
- **`services/llama_indexing_service.py`**: Builds FAISS indices from documents in configurable paths.
- **`services/llm_client.py`**: Communicates with the LLM microservices for natural language processing tasks.
- **`services/llm_service.py`**: Provides methods for handling LLM interactions and conversation logging.
- **`services/llm_service_server.py`**: Sets up FastAPI server to expose LLM functions over HTTP.
- **`services/llm_streaming_client.py`**: Enhances LLMClient with streaming capabilities for real-time responses.
- **`services/llm_streaming_server.py`**: FastAPI-based OAuth streaming server to handle dynamic LLM interactions.
- **`services/logger.py`**: Implements loggers with custom formatting for structured logging.
- **`services/memory_logger.py`**: Logs system and process memory usage.
- **`services/microservices_loader.py`**: Load and manage microservices for the voice assistant.
- **`services/service_manager.py`**: Oversee starting, stopping, and monitoring the health of microservices.
- **`services/stt_client.py`**: HTTP client for the STT microservices, mimicking expected interface.
- **`services/stt_service.py`**: Manages speech-to-text functions including dynamic RMS management.
- **`services/stt_service_server.py`**: Provides HTTP endpoints for speech-to-text.
- **`services/tts_client.py`**: HTTP client to communicate with a TTS microservice.
- **`services/tts_service.py`**: Converts text inputs into speech; manages audio chunk playback.
- **`services/tts_service_server.py`**: FastAPI server managing TTS tasks.
- **`services/tts_streaming_client.py`**: Client for streaming text-to-speech operations.
- **`services/web_search_service.py`**: Integrates web search capabilities with third-party APIs.

### Handlers
- **`services/handlers/file_search_handler.py`**: Conducts file searches across specified paths.
- **`services/handlers/memory_handler.py`**: Manages persistent memory operations like storing reminders.
- **`services/handlers/note_handler.py`**: Allows users to create, list, and delete text notes.
- **`services/handlers/web_search_handler.py`**: Interacts with web services to gather and summarize information.

### Utilities
- **`services/llm_text.py`**: Manages text and response templates for localization.

## 2. File Call Relationships

- **`main.py`** initializes and manages calls to most services including STT, TTS, and handlers.
- **`streaming_main_handler.py`** calls audio stream functions from `main.py`.
- **Handlers** call respective service methods, e.g., `note_handler` updates files and memory.

## 3. Method Explanations

- **`DynamicRMSService.start()`**: Initiates RMS monitoring.
- **`LLMService.get_response(prompt)`**: Processes language input using the LLM model.
- **`TTSService.speak(text)`**: Converts text to synthesized speech, playing via audio queue.

## 4. Class Explanations

- **`DynamicRMSService`**: Calculates audio levels to provide threshold adjustments for VAD.
- **`LLMService`**: Manages conversations using LLM, including dialog logging and intent handling.
- **`STTService`**: Uses time efficient models to transcribe spoken language to text reliably.

## 5. Data Flows

- **Input**: Audio data captured via streaming, processed through VAD and wake word detection.
- **Processing**: Guided by detected intents, parsed using LLM, results dispatched through handlers.
- **Output**: Cmds executed, results vocalized through TTS synthesis.

## 6. Loops

- **Audio Listening Loop**: Found in `main.py`, repeats reading audio chunks and monitoring wake words.

## 7. Variables

- **`stream` in `audio_stream_manager()`**: Manages the flow of audio data in real-time.
- **`vad` in `STTService`**: Allocates a VAD object for checking continuous voice activity.

## 8. Processes

- **Service Initialization**: Each service starts in an isolated thread or subprocess to ensure concurrency.
- **Indexing**: The `llama_indexing_service.py` handles reading and structuring large volumes of documents into searchable vectors.



```

---

## File: `docs/codebase_map.md`

**Path:** `docs/codebase_map.md`

```

```

---

## File: `docs/project_inventory.txt`

**Path:** `docs/project_inventory.txt`

```
# Project Python Files Inventory
Generated on: Wed Jul 30 10:45:03 PM EEST 2025

## Summary
- Root files: 4
- Service files: 24 (20 services + 4 handlers)
- Test files: 12
- Total Python files: 40

## Root Directory Python Files (4)
1. main.py - Main application entry point
2. manage_logs.py - Log management utility
3. test_logging.py - Logging test script
4. test_tts.py - TTS test script

## Services Directory Python Files (20)
### Core Services
1. services/__init__.py
2. services/dashboard.py
3. services/dynamic_rms_service.py - ✅ TESTED (stub)
4. services/exceptions.py
5. services/intent_detector.py - ✅ TESTED (stub)
6. services/kwd_service.py - ✅ FULLY TESTED WITH REAL INTEGRATION
7. services/loader.py
8. services/logger.py - ✅ TESTED (stub)
9. services/memory_logger.py
10. services/microservices_loader.py
11. services/service_manager.py - ✅ TESTED (stub)
12. services/web_search_service.py

### LLM Services
13. services/llama_file_search_service.py
14. services/llama_indexing_service.py
15. services/llm_client.py
16. services/llm_service.py - ✅ TESTED (stub)
17. services/llm_service_server.py - ✅ TESTED (stub)
18. services/llm_text.py

### STT/TTS Services
19. services/stt_client.py
20. services/stt_service.py - ✅ TESTED (stub)
21. services/stt_service_server.py - ✅ TESTED (stub)
22. services/tts_client.py
23. services/tts_service.py - ✅ TESTED (stub)
24. services/tts_service_server.py - ✅ TESTED (stub)

## Services/Handlers Directory Python Files (4)
1. services/handlers/file_search_handler.py
2. services/handlers/memory_handler.py
3. services/handlers/note_handler.py
4. services/handlers/web_search_handler.py

## Tests Directory Python Files (12)
1. tests/__init__.py
2. tests/dynamic_rms_service_test.py - For: dynamic_rms_service.py
3. tests/intent_detector_test.py - For: intent_detector.py
4. tests/kwd_service_test.py - For: kwd_service.py ✅ COMPLETE
5. tests/llm_service_server_test.py - For: llm_service_server.py
6. tests/llm_service_test.py - For: llm_service.py
7. tests/logger_test.py - For: logger.py
8. tests/service_manager_test.py - For: service_manager.py
9. tests/stt_service_server_test.py - For: stt_service_server.py
10. tests/stt_service_test.py - For: stt_service.py
11. tests/tts_service_server_test.py - For: tts_service_server.py
12. tests/tts_service_test.py - For: tts_service.py

## Services Without Tests (12)
- dashboard.py
- exceptions.py
- llama_file_search_service.py
- llama_indexing_service.py
- llm_client.py
- llm_text.py
- loader.py
- memory_logger.py
- microservices_loader.py
- web_search_service.py
- All 4 handler files

## Quick Reference
- ✅ Fully tested: kwd_service.py
- ✅ Test stubs exist: 11 services
- ❌ No tests: 12 services

```

---

## File: `docs/project_map.md`

**Path:** `docs/project_map.md`

```
# Codebase Map

## Table of Contents
- [📁 File List](#-file-list)
- [🏛️ Class Diagram](#🏛️-class-diagram)
- [🔧 Method Map](#🔧-method-map)
- [🧩 Service Inventory](#🧩-service-inventory)
- [🔄 Data Flow Diagram](#🔄-data-flow-diagram)
- [📦 Dependency Map](#📦-dependency-map)
- [🚀 Entry Points](#🚀-entry-points)
- [📈 Call Graph Summary](#📈-call-graph-summary)

## 📁 File List
- Root Directory
  - `main.py`
  - `streaming_main_handler.py`

- Services Directory
  - `services/__init__.py`
  - `services/dynamic_rms_service.py`
  - `services/exceptions.py`
  - `services/handlers/file_search_handler.py`
  - `services/handlers/memory_handler.py`
  - `services/handlers/note_handler.py`
  - `services/handlers/web_search_handler.py`
  - `services/intent_detector.py`
  - `services/kwd_service.py`
  - `services/llama_file_search_service.py`
  - `services/llama_indexing_service.py`
  - `services/llm_client.py`
  - `services/llm_service.py`
  - `services/llm_service_server.py`
  - `services/llm_streaming_client.py`
  - `services/llm_streaming_server.py`
  - `services/llm_text.py`
  - `services/logger.py`
  - `services/memory_logger.py`
  - `services/microservices_loader.py`
  - `services/service_manager.py`
  - `services/stt_client.py`
  - `services/stt_service.py`
  - `services/stt_service_server.py`
  - `services/tts_client.py`
  - `services/tts_service.py`
  - `services/tts_service_server.py`
  - `services/tts_streaming_client.py`
  - `services/web_search_service.py`

## 🏛️ Class Diagram
### `main.py`
- **play_beep**: Plays a sound on wake word detection.
- **handle_wake_word_interaction**: Manages interaction after wake word.
- **handle_followup_conversation**: Continues conversation post-wake word.

### `streaming_main_handler.py`
- **handle_wake_word_interaction_streaming**: Enhanced interaction handler with streaming.
- **handle_followup_conversation_streaming**: Follows up with streaming.
  
### Services
#### `KWDService`
- **process_audio**: Processes audio for wake word detection.

#### `LLMService`
- Manages language model interactions and intent detection.
  
#### `STTService`
- Transcribes speech to text with Whisper and other tools.
  
#### `TTSService`
- Converts text to speech using Kokoro.

#### `MemoryLogger`
- Logs memory usage of specified processes.

#### `NoteHandler`
- Handles note-taking commands.

#### `WebSearchHandler`
- Manages web search interactions.

## 🔧 Method Map
### `main.py`
- **play_beep**: Initiates a non-blocking thread to play a sound file.
- **handle_wake_word_interaction**: Uses services like `stt_service` and `llm_service` to respond to audio prompts.
- **record_audio_for_transcription**: Records audio until silence is detected.

### Services
#### `KWDService`
- **enable/disable**: Toggles activation of wake word detection.
- **process_audio**: Uses VAD and model to detect wake words.

#### `LLMService`
- **get_response**: Generates a response to user input.
- **_load_memory**: Loads memory from a file.
  
#### `STTService`
- **listen_and_transcribe**: Records and transcribes spoken commands.
- **_transcribe_audio**: Transcribes audio using the Whisper model.

## 🧩 Service Inventory
- **LLM Service**: Language model interactions.
- **STT Service**: Speech-to-text processing.
- **TTS Service**: Text-to-speech synthesis.
- **Dynamic RMS**: Adaptive audio thresholding.

## 🔄 Data Flow Diagram
- **Input**: Audio captured via PyAudio.
- **Processing**: Audio processed by VAD and RMS for event detection.
- **Interaction**: Via HTTP APIs, converted to text, processed by LLM.
- **Output**: Text played back as audio via TTS.

## 📦 Dependency Map
- **Imports**: Extensive use of libraries like `pyaudio`, `numpy`, `uvicorn`, `fastapi`.
- **Data Flow**: Services interact through HTTP APIs, managed by `service_manager`.

## 🚀 Entry Points
- **CLI**: `main.py`, `streaming_main_handler.py`.
- **API**: Streaming via HTTP in `llm_service_server.py`, `stt_service_server.py`, `tts_service_server.py`.

## 📈 Call Graph Summary
- **Initialization**: Services initiated on application start.
- **Operation**: Continuous processing and response generation loop.
- **Shutdown**: Graceful cleanup of services and resources on exit.


```

---

## File: `docs/project_structure.txt`

**Path:** `docs/project_structure.txt`

```
/home/master/Projects/test/config/llm_responses.json
/home/master/Projects/test/config/notes.json
/home/master/Projects/test/config/search_config.json
/home/master/Projects/test/config/sounds/kwd_success.wav
/home/master/Projects/test/config/system_prompt.txt
/home/master/Projects/test/LOGGING.md
/home/master/Projects/test/main.py
/home/master/Projects/test/manage_logs.py
/home/master/Projects/test/project_structure.txt
/home/master/Projects/test/.pytest_cache/README.md
/home/master/Projects/test/README.md
/home/master/Projects/test/recordings/kwd_clips/20250730_153645_138_buffer.wav
/home/master/Projects/test/recordings/kwd_clips/20250730_153646_568_buffer.wav
/home/master/Projects/test/recordings/kwd_clips/20250730_153648_594_buffer.wav
/home/master/Projects/test/recordings/kwd_clips/20250730_153650_792_buffer.wav
/home/master/Projects/test/recordings/kwd_clips/20250730_153653_374_buffer.wav
/home/master/Projects/test/recordings/kwd_clips/20250730_153656_467_buffer.wav
/home/master/Projects/test/recordings/kwd_clips/20250730_153657_299_buffer.wav
/home/master/Projects/test/recordings/kwd_clips/20250730_153659_261_buffer.wav
/home/master/Projects/test/recordings/kwd_clips/20250730_153700_904_buffer.wav
/home/master/Projects/test/recordings/kwd_clips/20250730_153707_411_buffer.wav
/home/master/Projects/test/recordings/kwd_clips/20250730_212122_148_buffer.wav
/home/master/Projects/test/recordings/kwd_clips/20250730_212123_730_buffer.wav
/home/master/Projects/test/recordings/kwd_clips/20250730_212125_757_buffer.wav
/home/master/Projects/test/recordings/kwd_clips/20250730_212127_441_buffer.wav
/home/master/Projects/test/recordings/kwd_clips/20250730_212129_809_buffer.wav
/home/master/Projects/test/requirements.txt
/home/master/Projects/test/services/dashboard.py
/home/master/Projects/test/services/dynamic_rms_service.py
/home/master/Projects/test/services/exceptions.py
/home/master/Projects/test/services/handlers/file_search_handler.py
/home/master/Projects/test/services/handlers/memory_handler.py
/home/master/Projects/test/services/handlers/note_handler.py
/home/master/Projects/test/services/handlers/web_search_handler.py
/home/master/Projects/test/services/__init__.py
/home/master/Projects/test/services/intent_detector.py
/home/master/Projects/test/services/kwd_service.py
/home/master/Projects/test/services/llama_file_search_service.py
/home/master/Projects/test/services/llama_indexing_service.py
/home/master/Projects/test/services/llm_client.py
/home/master/Projects/test/services/llm_service.py
/home/master/Projects/test/services/llm_service_server.py
/home/master/Projects/test/services/llm_text.py
/home/master/Projects/test/services/loader.py
/home/master/Projects/test/services/logger.py
/home/master/Projects/test/services.md
/home/master/Projects/test/services/memory_logger.py
/home/master/Projects/test/services/microservices_loader.py
/home/master/Projects/test/services/service_manager.py
/home/master/Projects/test/services/stt_client.py
/home/master/Projects/test/services/stt_service.py
/home/master/Projects/test/services/stt_service_server.py
/home/master/Projects/test/services/tts_client.py
/home/master/Projects/test/services/tts_service.py
/home/master/Projects/test/services/tts_service_server.py
/home/master/Projects/test/services/web_search_service.py
/home/master/Projects/test/sounds/kwd_success.mp3
/home/master/Projects/test/sounds/kwd_success.wav
/home/master/Projects/test/test_logging.py
/home/master/Projects/test/tests/dynamic_rms_service_test.py
/home/master/Projects/test/tests/__init__.py
/home/master/Projects/test/tests/intent_detector_test.py
/home/master/Projects/test/tests/kwd_service_test.py
/home/master/Projects/test/tests/llm_service_server_test.py
/home/master/Projects/test/tests/llm_service_test.py
/home/master/Projects/test/tests/logger_test.py
/home/master/Projects/test/tests/README.md
/home/master/Projects/test/tests/service_manager_test.py
/home/master/Projects/test/tests/stt_service_server_test.py
/home/master/Projects/test/tests/stt_service_test.py
/home/master/Projects/test/tests/tests/main_test.py
/home/master/Projects/test/tests/tts_service_server_test.py
/home/master/Projects/test/tests/tts_service_test.py
/home/master/Projects/test/test_tts.py

```

---

## File: `docs/project_tree.txt`

**Path:** `docs/project_tree.txt`

```

```

---

## File: `docs/prompt.txt`

**Path:** `docs/prompt.txt`

```
You are an advanced static code analysis expert and reverse engineer.

You will receive the full contents of all `.py` files from a Python project (limited to the root directory and `/services/`). Your job is to **extract every relationship, class, method, call, and data flow** and output a **structured, detailed, and human-usable Markdown document** for future debugging and development.

🚫 You are not allowed to make vague summaries like:
- “This file imports several modules...”
- “This class handles input...”
- “This method seems to do something...”

✅ Instead, **you must provide line-specific**, **file-specific**, and **function-specific** insights based purely on the code you are shown.

---

## 🔍 TASKS:

### 1. 📁 **File Index**
- List all scanned `.py` files, including full relative paths.

### 2. 🧱 **Classes & Methods Breakdown**
- For each file, list all defined classes.
  - Under each class:
    - List method names with line numbers
    - Summarize their logic and behavior based on implementation
    - Note internal state/attributes set during `__init__` or elsewhere
    - List decorators used (e.g., `@app.post`, `@classmethod`, etc.)

### 3. 🧠 **Function Analysis**
- For all standalone functions:
  - Show name, file, line number
  - Describe its inputs, outputs, and what it actually does (based on body and comments)
  - If it calls other functions, name them

### 4. 🔧 **Services Map**
- Detect and list all classes with the suffix `Service` or located under `/services/`
- For each:
  - What is its responsibility?
  - What other files/functions/services does it call or depend on?
  - Are they synchronous or async?
  - Are they exposing APIs (FastAPI routes, etc.)?

### 5. 🔄 **Data Flow**
- Trace how data enters the system (e.g., HTTP POST, audio input, CLI arg)
- How it is processed (by which function/class), and where it flows next
- Follow it until it’s either:
  - Returned to user
  - Saved to disk
  - Logged
  - Queued or handed to another service

### 6. 🔗 **Dependency Map**
- For each file:
  - List exactly which modules/files it imports (e.g., `from services.tts_service import TTSService`)
  - List which **classes/functions** it uses from each import (do not generalize)

### 7. 🚀 **Entry Points**
- Identify main execution paths:
  - Main scripts (e.g., `if __name__ == "__main__"`)
  - HTTP endpoints (`@app.get`, etc.)
  - CLI entry methods
  - Background jobs or threaded daemons

### 8. 📈 **Call Graph**
- List the most important execution flows from start to end:
  - What starts first?
  - Which services are invoked?
  - Which subprocesses or threads are spawned?

---

## ⛔️ INSTRUCTIONS:

- Do not summarize — describe.
- Be specific and technical.
- If any part of a function or class is unclear, output `[UNRESOLVED]` and move on.
- Use a **clean Markdown layout** with:
  - Section headings
  - Code blocks for snippets
  - Links in the Table of Contents
- Do not hallucinate. Only describe what is explicitly present in the source.

---

## 📁 Output Format: `codebase_map.md`

```

---

## File: `docs/services.md`

**Path:** `docs/services.md`

```
# Services Test Status

This document tracks the testing status of all services in the project.

| Service | Test File | Test Status |
|---------|-----------|-------------|
| dashboard.py | - | Not tested |
| dynamic_rms_service.py | dynamic_rms_service_test.py | Created (stub) |
| exceptions.py | - | Not tested |
| intent_detector.py | intent_detector_test.py | Created (stub) |
| **kwd_service.py** | **kwd_service_test.py** | **✅ Success** |
| llama_file_search_service.py | - | Not tested |
| llama_indexing_service.py | - | Not tested |
| llm_client.py | - | Not tested |
| llm_service.py | llm_service_test.py | Created (stub) |
| llm_service_server.py | llm_service_server_test.py | Created (stub) |
| llm_text.py | - | Not tested |
| loader.py | - | Not tested |
| logger.py | logger_test.py | Created (stub) |
| memory_logger.py | - | Not tested |
| microservices_loader.py | - | Not tested |
| service_manager.py | service_manager_test.py | Created (stub) |
| stt_client.py | - | Not tested |
| **stt_service.py** | **stt_service_comprehensive_test.py** | **✅ Success** |
| stt_service_server.py | stt_service_server_test.py | Created (stub) |
| **tts_client.py** | **tts_microservice_test.py** | **✅ Success** |
| **tts_service.py** | **tts_service_test.py** | **✅ Success** |
| **tts_service_server.py** | **tts_service_server_test.py** | **✅ Success** |
| web_search_service.py | - | Not tested |

## Handlers

| Handler | Test File | Test Status |
|---------|-----------|-------------|
| handlers/file_search_handler.py | - | Not tested |
| handlers/memory_handler.py | - | Not tested |
| handlers/note_handler.py | - | Not tested |
| handlers/web_search_handler.py | - | Not tested |

## Test Status Legend

- **✅ Success**: Full test suite implemented and passing (including unit tests, mocks, and real integration tests)
- **Created (stub)**: Test file exists but only contains stub/placeholder content
- **Not tested**: No test file exists

## Notes

### KWD Service Test Success Details
The KWD (Keyword Detection) service has been fully tested with:
- Comprehensive unit tests with mocked components
- Edge case handling (empty audio, buffer management, multiple wake words)
- Real microphone integration test with actual OpenWakeWord model
- Cooldown functionality to prevent multiple detections from single utterance
- Dynamic RMS threshold adjustment
- Audio feedback (beep sound) on detection

All tests pass successfully, demonstrating the service's reliability in both isolated and real-world scenarios.

### TTS Service Test Success Details
The TTS (Text-to-Speech) service has been fully tested with:
- Comprehensive stress testing with VRAM constraints (1.5GB free)
- Real audio output verification with 10-sentence long text
- VRAM monitoring during playback showing stable memory usage (0.53GB allocated, 8% GPU utilization)
- Text chunking and buffering validation for seamless audio playback
- GPU memory management under constrained conditions
- Error handling and recovery mechanisms
- Threading performance for concurrent audio generation and playback
- Fixed critical API bug (tokenizer attribute issue) during testing

The service completed a 60-second stress test successfully with consistent memory usage and high-quality audio output.

### TTS Client & Server Test Success Details
The TTS microservice architecture (client + server) has been fully tested with:
- Complete microservice integration testing (client ↔ server ↔ service)
- HTTP API endpoint validation (/speak, /warmup, /health)
- Latency monitoring and performance measurement
- Server startup/shutdown lifecycle management
- Client connection handling and error recovery
- Short and long text processing through HTTP layer
- Network timeout handling and graceful degradation
- Process isolation and resource cleanup
- Added immediate playback stop functionality to core service

The microservice test validates the full distributed architecture with proper client-server communication.

### STT Service Test Success Details
The STT (Speech-to-Text) service has been comprehensively tested with:
- **CUDA Support**: Verified GPU acceleration with NVIDIA RTX A2000 (7.8GB VRAM)
- **Model Optimization**: Updated to use `small.en` model with optimized English transcription
- **VRAM Monitoring**: Real-time memory tracking (min/max: 1.561GB - 1.643GB)
- **GPU Utilization**: Peak utilization up to 97% during transcription
- **Performance Benchmarking**: 0.12x average real-time processing (much faster than playback)
- **Memory Management**: Zero memory leaks, stable 0.903GB model footprint
- **Model Scaling**: Tested tiny (0.142GB), base (0.272GB), and small (0.903GB) models
- **Edge Case Handling**: Proper handling of empty, malformed, and very short audio
- **Long Audio Processing**: Successfully processed 10-second audio in 6.43s (0.64x real-time)
- **Stress Testing**: Sequential rapid processing validated memory stability
- **Task Optimization**: Uses `task="transcribe"` for better English performance

The service demonstrates excellent real-time performance with GPU acceleration, processing audio significantly faster than playback speed while maintaining stable VRAM usage.

## Quick Reference
- ✅ Fully tested: kwd_service.py, stt_service.py, tts_service.py, tts_client.py, tts_service_server.py
- ✅ Test stubs exist: 7 services
- ❌ No tests: 11 services

```

---

## File: `main.py`

**Path:** `main.py`

```
# Suppress common warnings at the very beginning
import warnings
import os
warnings.filterwarnings("ignore", message="pkg_resources is deprecated")

# Suppress ALSA/JACK warnings safely
os.environ['ALSA_SUPPRESS_ERRORS'] = '1'
os.environ['JACK_NO_START_SERVER'] = '1'

import pyaudio
import sys
import logging
import argparse
from datetime import datetime
import time
import subprocess
from contextlib import contextmanager
import webrtcvad
import numpy as np
import threading

# Import from the services package
from services.microservices_loader import load_services_microservices
from services.kwd_service import KWDService
from services.logger import app_logger
from services.memory_logger import MemoryLogger
from services.dynamic_rms_service import DynamicRMSService
from services.llm_streaming_client import StreamingTTSIntegration
from services.exceptions import (
    MicrophoneException, 
    ServiceInitializationException, 
    AudioException,
    VoiceAssistantException
)

def play_beep(log=None):
    """Play the wake word detection sound."""
    def _beep():
        try:
            # Path to the wake word success sound
            sound_file = os.path.join(os.path.dirname(__file__), "config", "sounds", "kwd_success.wav")
            
            if log:
                log.debug(f"Playing wake word detection sound: {sound_file}")
            
            # Check if file exists
            if not os.path.exists(sound_file):
                if log:
                    log.warning(f"Sound file not found: {sound_file}")
                return  # Just return, don't play anything if file is missing
            
            # Try multiple audio methods with better error handling and maximum volume
            audio_methods = [
                f"paplay --volume=65536 '{sound_file}'",  # Max volume for paplay
                f"aplay -q '{sound_file}'",
                f"ffplay -nodisp -autoexit -volume 100 '{sound_file}' 2>/dev/null"
            ]
            
            for method in audio_methods:
                try:
                    if log:
                        log.debug(f"Trying audio method: {method}")
                    result = subprocess.run(method, shell=True, timeout=3, 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        if log:
                            log.debug(f"Successfully played sound with: {method.split()[0]}")
                        return
                    else:
                        if log:
                            log.debug(f"Method failed with return code {result.returncode}: {result.stderr}")
                except subprocess.TimeoutExpired:
                    if log:
                        log.debug(f"Audio method timed out: {method}")
                except Exception as e:
                    if log:
                        log.debug(f"Audio method exception {method}: {e}")
            
            if log:
                log.debug("All audio methods failed")
            
        except Exception as e:
            if log:
                log.debug(f"Could not play wake word sound: {e}")
    
    # Run beep in a separate thread to avoid blocking
    threading.Thread(target=_beep, daemon=True).start()

@contextmanager
def suppress_stderr():
    """Temporarily suppress stderr to hide ALSA/JACK warnings."""
    # Save the original stderr file descriptor
    stderr_fd = sys.stderr.fileno()
    old_stderr_fd = os.dup(stderr_fd)
    
    try:
        # Redirect stderr to /dev/null
        devnull_fd = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull_fd, stderr_fd)
        os.close(devnull_fd)
        yield
    finally:
        # Restore original stderr
        os.dup2(old_stderr_fd, stderr_fd)
        os.close(old_stderr_fd)

@contextmanager
def audio_stream_manager(format_type, channels, rate, frames_per_buffer):
    """Context manager for PyAudio stream with proper cleanup."""
    pa = None
    stream = None
    try:
        # Suppress ALSA/JACK warnings during PyAudio initialization
        with suppress_stderr():
            pa = pyaudio.PyAudio()
            stream = pa.open(
                format=format_type, 
                channels=channels, 
                rate=rate, 
                input=True, 
                frames_per_buffer=frames_per_buffer
            )
        yield stream
    except Exception as e:
        raise MicrophoneException(
            f"Could not open microphone stream: {e}",
            context={"error": str(e), "format": format_type, "rate": rate}
        )
    finally:
        if stream and stream.is_active():
            stream.stop_stream()
            stream.close()
        if pa:
            with suppress_stderr():
                pa.terminate()


def record_audio_for_transcription(stream, timeout_ms=3000, log=None):
    """Record audio from stream until silence is detected."""
    vad = webrtcvad.Vad(3)
    recorded_frames = []
    silence_duration_ms = 0
    VAD_FRAME_MS = 30
    VAD_FRAME_SAMPLES = int(16000 * 0.03)  # 30ms at 16kHz
    MAX_INT16 = 32767.0
    
    if log:
        log.info("Recording audio for transcription...")
    
    while True:
        try:
            audio_chunk = stream.read(VAD_FRAME_SAMPLES, exception_on_overflow=False)
            recorded_frames.append(audio_chunk)
            
            # Simple VAD check
            chunk_np = np.frombuffer(audio_chunk, dtype=np.int16)
            normalized_chunk = chunk_np.astype(np.float32) / MAX_INT16
            rms = np.sqrt(np.mean(normalized_chunk**2))
            
            try:
                is_speech = vad.is_speech(audio_chunk, sample_rate=16000) and (rms > 0.15)
            except Exception as e:
                if log:
                    log.debug(f"VAD error: {e}, using RMS fallback")
                is_speech = rms > 0.15
            
            if is_speech:
                silence_duration_ms = 0
            else:
                silence_duration_ms += VAD_FRAME_MS
                if silence_duration_ms >= timeout_ms:
                    if log:
                        log.debug("Silence detected, finishing recording")
                    break
                    
        except Exception as e:
            if log:
                log.error(f"Error reading audio: {e}")
            break
    
    return b''.join(recorded_frames)


def handle_wake_word_interaction(stt_service, llm_service, tts_service, log):
    """Handle the interaction after wake word detection."""
    try:
        log.info("Starting transcription after wake word detection")
        
        with audio_stream_manager(
            pyaudio.paInt16, 1, 16000, int(16000 * 0.03)
        ) as stream:
            audio_data = record_audio_for_transcription(stream, timeout_ms=3000, log=log)
        
        if not audio_data:
            log.warning("No audio data recorded")
            return
            
        transcription = stt_service.transcribe_audio_bytes(audio_data)
        
        if not transcription:
            log.warning("STT service returned no transcription")
            return
        
        speech_end_time = time.time()
        log.info(f"Transcription received: {transcription}")
        
        tts_start_time = time.time()
        log.info(f"LLM Query: {transcription}")
        
        try:
            # ✅ Replaced bridge with StreamingTTSIntegration
            integration = StreamingTTSIntegration(llm_service, tts_service, min_chunk_size=80)
            integration.speak_streaming_response(transcription)
            log.info("Streaming LLM to TTS completed")
            
        except Exception as e:
            log.warning(f"Streaming failed, falling back: {e}")
            llm_result = llm_service.get_response(transcription)
            llm_response = llm_result[0] if isinstance(llm_result, tuple) else llm_result
            tts_service.speak(llm_response)

        speech_to_tts_time = tts_start_time - speech_end_time
        log.info(f"Speech→TTS latency: {speech_to_tts_time:.2f}s")
        app_logger.log_performance("speech_to_tts", speech_to_tts_time)
        
        handle_followup_conversation(stt_service, llm_service, tts_service, log)
        log.info("Conversation ended - listening for wake word again")
        
    except Exception as e:
        log.error(f"Error during wake word interaction: {e}", exc_info=True)


def handle_followup_conversation(stt_service, llm_service, tts_service, log):
    """Handle the follow-up conversation loop."""
    while True:
        try:
            log.debug("Listening for follow-up...")
            
            with audio_stream_manager(
                pyaudio.paInt16, 1, 16000, int(16000 * 0.03)
            ) as stream:
                audio_data = record_audio_for_transcription(stream, timeout_ms=4000, log=log)
            
            if not audio_data:
                log.info("Dialog ended due to inactivity")
                break
                
            follow_up = stt_service.transcribe_audio_bytes(audio_data)
            
            if not follow_up:
                log.info("Dialog ended due to inactivity")
                break
                
            speech_end_time = time.time()
            log.info(f"Follow-up transcription: {follow_up}")
            tts_start_time = time.time()
            
            try:
                # ✅ Replaced bridge with StreamingTTSIntegration
                integration = StreamingTTSIntegration(llm_service, tts_service, min_chunk_size=80)
                integration.speak_streaming_response(follow_up)
                log.info("Streaming follow-up LLM to TTS completed")
                
            except Exception as e:
                log.debug(f"Follow-up streaming failed, fallback: {e}")
                llm_result = llm_service.get_response(follow_up)
                llm_response = llm_result[0] if isinstance(llm_result, tuple) else llm_result
                tts_service.speak(llm_response)
            
            app_logger.log_performance("followup_speech_to_tts", tts_start_time - speech_end_time)
            
        except Exception as e:
            log.error(f"Error during follow-up conversation: {e}", exc_info=True)
            break


def run_indexing():
    """Run the file indexing process using LlamaIndex."""
    print("[INFO] Starting file indexing with LlamaIndex...")
    try:
        from services.llama_indexing_service import LlamaIndexingService
        indexer = LlamaIndexingService()
        indexer.build_and_save_index()
        print("[INFO] Indexing completed successfully.")
    except Exception as e:
        print(f"[ERROR] Indexing failed: {e}")
        sys.exit(1)

def main():
    """Main application entry point with enhanced error handling."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Voice Assistant with File Search")
    parser.add_argument("--index", action="store_true", help="Run file indexing and exit")
    args = parser.parse_args()
    
    # If indexing is requested, run it and exit
    if args.index:
        run_indexing()
        return
    
    app_start_time = time.time()
    log = app_logger.get_logger("main")
    mem_logger = None
    
    # Configuration
    CONFIG = {
        "format": pyaudio.paInt16,
        "channels": 1,
        "rate": 16000,
        "vad_frame_ms": 30,
        "wakeword_threshold": 0.5
    }
    CONFIG["vad_frame_samples"] = int(CONFIG["rate"] * (CONFIG["vad_frame_ms"] / 1000.0))
    
    try:
        log.info("Starting Alexa - Local voice assistant")
        
        # Start memory logging (temporarily disabled to test segfault)
        # mem_logger = MemoryLogger()
        # mem_logger.start()
        mem_logger = None
        
        # Load services with detailed error handling
        log.info("Loading services...")
        service_manager = None
        try:
            vad, oww_model, stt_service, llm_service, tts_service, dynamic_rms, service_manager = load_services_microservices()
            kwd_service = KWDService(oww_model, vad, dynamic_rms)
            # Enable KWD after successful initialization
            kwd_service.enable()
        except Exception as e:
            raise ServiceInitializationException(
                "services", 
                f"Failed to load core services: {str(e)}",
                context={"startup_time_ms": (time.time() - app_start_time) * 1000}
            )
        
        # Log startup performance
        kwd_ready_time = time.time()
        startup_duration = kwd_ready_time - app_start_time
        app_logger.log_performance(
            "app_startup", 
            startup_duration,
            {"services_loaded": 6}
        )
        
        log.info(f"Services loaded successfully in {startup_duration:.2f} seconds")
        
        # Announce readiness
        try:
            tts_service.speak("Hi Master! Alexa at your services.")
        except Exception as e:
            log.warning(f"Could not announce readiness: {e}")
            
        
        log.info("Voice assistant ready - listening for wake word...")
        
        # Main application loop with audio stream management
        with audio_stream_manager(
            CONFIG["format"], 
            CONFIG["channels"], 
            CONFIG["rate"], 
            CONFIG["vad_frame_samples"]
        ) as stream:
            
            
            while True:
                try:
                    audio_chunk = stream.read(
                        CONFIG["vad_frame_samples"], 
                        exception_on_overflow=False
                    )
                    # Update dynamic RMS threshold with the same audio data
                    dynamic_rms.update_threshold(audio_chunk)
                    
                    # Process audio with wake word detection
                    prediction, utterance_buffer = kwd_service.process_audio(audio_chunk)
                    
                    # Handle wake word detection
                    if prediction:
                        log.info(f"Wake word detected! Confidence: {prediction}")
                        # Don't update intent here - let the wake word interaction handle it
                        handle_wake_word_interaction(stt_service, llm_service, tts_service, log)
                            
                except AudioException as e:
                    log.error(f"Audio processing error: {e}")
                    # if publisher:
                    #     publisher.publish({"state": "Audio Error"})
                    if not e.recoverable:
                        raise
                    # Continue for recoverable audio errors
                    time.sleep(0.1)
                    
                except Exception as e:
                    log.error(f"Unexpected error in main loop: {e}", exc_info=True)
                    # if publisher:
                    #     publisher.publish({"state": "Error"})
                    # Continue running - log error but don't crash
                    time.sleep(0.1)
    
    except KeyboardInterrupt:
        log.info("Received shutdown signal (Ctrl+C)")
    
    except VoiceAssistantException as e:
        app_logger.handle_exception(
            type(e), e, e.__traceback__, 
            context=e.context
        )
        sys.exit(1)
        
    except Exception as e:
        app_logger.handle_exception(
            type(e), e, e.__traceback__,
            context={"phase": "startup" if mem_logger is None else "runtime"}
        )
        sys.exit(1)
        
    finally:
        # Cleanup resources
        if mem_logger:
            mem_logger.stop()
        if service_manager:
            service_manager.stop_all_services()
        log.info("Voice Assistant shutting down...")
        
        # Move main_app.log to logs directory if it exists
        try:
            if os.path.exists('main_app.log'):
                os.makedirs('logs', exist_ok=True)
                if os.path.exists('logs/main_app.log'):
                    os.remove('logs/main_app.log')
                os.rename('main_app.log', 'logs/main_app.log')
        except Exception as e:
            print(f"Warning: Could not move main_app.log to logs directory: {e}")
        
        logging.shutdown()

if __name__ == '__main__':
    main()
```

---

## File: `requirements.txt`

**Path:** `requirements.txt`

```
# requirements.txt

# Audio Processing
pyaudio
webrtcvad
numpy

# Wake Word Detection
# Note: openwakeword has Python version constraints, skipping for now
# openwakeword==0.5.1
onnxruntime

# Whisper STT
torch
openai-whisper

# LLM via Ollama
ollama

# TTS via Kokoro
kokoro

# Logging and Utility
requests

# Dashboard and Monitoring
rich
psutil

# Vector Search and Embeddings
llama-index
faiss-cpu
sentence-transformers

```

---

## File: `services/__init__.py`

**Path:** `services/__init__.py`

```

```

---

## File: `services/dynamic_rms_service.py`

**Path:** `services/dynamic_rms_service.py`

```
import numpy as np
import threading
import time
import pyaudio
import webrtcvad

class DynamicRMSService:
    def __init__(self, sample_rate=16000, frame_ms=30, window_seconds=3, multiplier=2.0):
        self.sample_rate = sample_rate
        self.frame_samples = int(sample_rate * frame_ms / 1000)
        self.vad = webrtcvad.Vad(3)
        self.multiplier = multiplier
        self.locked = False
        self.rms_values = []
        self.window_size = int(window_seconds * 1000 / frame_ms)
        self.threshold = 0.15  # fallback default
        self.running = False
        self._lock = threading.Lock()

    def start(self):
        if self.running:
            return
        self.running = True
        # Background thread disabled to prevent PyAudio conflicts
        # The main application will call update_threshold() directly

    def stop(self):
        self.running = False

    def lock(self):
        with self._lock:
            self.locked = True

    def reset(self):
        with self._lock:
            self.locked = False
            self.rms_values.clear()

    def get_threshold(self):
        with self._lock:
            return self.threshold
    
    def update_threshold(self, audio_chunk):
        """Manually update threshold based on audio chunk from main application."""
        try:
            audio_np = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32) / 32767.0
            rms = np.sqrt(np.mean(audio_np**2))
            
            try:
                is_speech = self.vad.is_speech(audio_chunk, sample_rate=self.sample_rate)
            except Exception as e:
                print(f"[ERROR] VAD failure in RMS update: {e}")
                is_speech = False  # fallback
            
            with self._lock:
                if not self.locked and not is_speech:
                    self.rms_values.append(rms)
                    if len(self.rms_values) > self.window_size:
                        self.rms_values.pop(0)
                    if self.rms_values:
                        self.threshold = np.mean(self.rms_values) * self.multiplier
        except Exception as e:
            print(f"[ERROR] Failed to update RMS threshold: {e}")

    def _monitor_loop(self):
        # Disabled independent audio monitoring to prevent PyAudio conflicts
        # The main application will handle audio processing and call update_threshold() directly
        while self.running:
            time.sleep(0.1)  # Keep thread alive but don't do audio processing

```

---

## File: `services/exceptions.py`

**Path:** `services/exceptions.py`

```
"""
Custom exception classes for the voice assistant application.
Provides structured error handling with context and categorization.
"""

class VoiceAssistantException(Exception):
    """Base exception for all voice assistant errors."""
    
    def __init__(self, message: str, context: dict = None, recoverable: bool = True):
        super().__init__(message)
        self.context = context or {}
        self.recoverable = recoverable
        self.timestamp = None
    
    def __str__(self):
        base_msg = super().__str__()
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            return f"{base_msg} (Context: {context_str})"
        return base_msg


class AudioException(VoiceAssistantException):
    """Exceptions related to audio processing."""
    pass


class MicrophoneException(AudioException):
    """Microphone access or configuration errors."""
    pass


class STTException(VoiceAssistantException):
    """Speech-to-text service errors."""
    pass


class LLMException(VoiceAssistantException):
    """Large Language Model service errors."""
    pass


class TTSException(VoiceAssistantException):
    """Text-to-speech service errors."""
    pass


class WakeWordException(VoiceAssistantException):
    """Wake word detection errors."""
    pass


class ServiceInitializationException(VoiceAssistantException):
    """Service loading and initialization errors."""
    
    def __init__(self, service_name: str, message: str, context: dict = None):
        super().__init__(message, context, recoverable=False)
        self.service_name = service_name


class ConfigurationException(VoiceAssistantException):
    """Configuration and setup errors."""
    
    def __init__(self, message: str, config_key: str = None, context: dict = None):
        super().__init__(message, context, recoverable=False)
        self.config_key = config_key


class ResourceException(VoiceAssistantException):
    """Resource management errors (files, network, etc.)."""
    pass


class ValidationException(VoiceAssistantException):
    """Data validation errors."""
    pass

```

---

## File: `services/handlers/file_search_handler.py`

**Path:** `services/handlers/file_search_handler.py`

```
import subprocess
from pathlib import Path

class FileSearchHandler:
    def __init__(self, file_search_service, tts, text):
        self.search_service = file_search_service
        self.tts = tts
        self.text = text

    def handle(self, prompt: str) -> str:
        result = self.search_service.search(prompt)
        exact = result.get("exact_matches", [])
        fuzzy = result.get("fuzzy_matches", [])
        content = result.get("content_matches", [])
        all_found = result.get("all_results", [])

        if not all_found:
            reply = self.text.get("search.none")
            return reply

        count = len(all_found)
        spoken = self.text.format("search.found_prefix", count=count, plural="s" if count != 1 else "")
        reply = spoken + "\n"

        if content:
            reply += "- In file content:\n" + "\n".join(f"  - {f}" for f in content[:5]) + "\n"
        if exact:
            reply += "- Exact filenames:\n" + "\n".join(f"  - {f}" for f in exact[:5]) + "\n"
        if fuzzy:
            reply += "- Fuzzy matches:\n" + "\n".join(f"  - {f}" for f in fuzzy[:5]) + "\n"

        if count == 1:
            subprocess.run(["xdg-open", all_found[0]], check=False)

        # Return what should be spoken
        if count <= 3:
            spoken_details = spoken + " " + ". ".join(Path(f).stem for f in all_found)
            return spoken_details
        else:
            return reply

```

---

## File: `services/handlers/memory_handler.py`

**Path:** `services/handlers/memory_handler.py`

```
import re
import os

class MemoryHandler:
    def __init__(self, memory_file_path, text):
        self.memory_file_path = memory_file_path
        self.text = text
        self._ensure_file()
        self.memories = self._load()

    def _ensure_file(self):
        os.makedirs(os.path.dirname(self.memory_file_path), exist_ok=True)
        if not os.path.exists(self.memory_file_path):
            with open(self.memory_file_path, 'w'): pass

    def _load(self):
        with open(self.memory_file_path, 'r') as f:
            return [line.strip() for line in f if line.strip()]

    def _save(self):
        with open(self.memory_file_path, 'w') as f:
            f.write('\n'.join(self.memories) + '\n')

    def can_handle(self, prompt: str) -> bool:
        return bool(re.search(r"(remember to|update memory|remove memory|list memories)", prompt, re.IGNORECASE))

    def handle(self, prompt: str) -> str:
        if m := re.search(r"remember to (.+)", prompt, re.IGNORECASE):
            self.memories.append(m.group(1).strip())
            self._save()
            return self.text.get("memory.add")

        if m := re.search(r"update memory (\d+) to (.+)", prompt, re.IGNORECASE):
            idx = int(m.group(1)) - 1
            if 0 <= idx < len(self.memories):
                self.memories[idx] = m.group(2).strip()
                self._save()
                return self.text.format("memory.update", index=idx + 1)
            return self.text.get("memory.missing")

        if m := re.search(r"remove memory (\d+)", prompt, re.IGNORECASE):
            idx = int(m.group(1)) - 1
            if 0 <= idx < len(self.memories):
                self.memories.pop(idx)
                self._save()
                return self.text.format("memory.remove", index=idx + 1)
            return self.text.get("memory.missing")

        if re.search(r"list memories", prompt, re.IGNORECASE):
            if not self.memories:
                return self.text.get("memory.empty")
            return self.text.get("memory.list_prefix") + "\n" + '\n'.join(
                [f"{i+1}. {m}" for i, m in enumerate(self.memories)])

        return ""

```

---

## File: `services/handlers/note_handler.py`

**Path:** `services/handlers/note_handler.py`

```
import re
import os
from datetime import datetime

class NoteHandler:
    def __init__(self, note_path="config/notes.json"):
        self.path = note_path
        self._ensure_file()
        self.notes = self._load()

    def _ensure_file(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        if not os.path.exists(self.path):
            with open(self.path, "w") as f:
                f.write("[]")

    def _load(self):
        import json
        with open(self.path, "r") as f:
            return json.load(f)

    def _save(self):
        import json
        with open(self.path, "w") as f:
            json.dump(self.notes, f, indent=2)

    def can_handle(self, prompt):
        return bool(re.search(r"\b(note|notes|take a note|delete note|show notes)\b", prompt, re.IGNORECASE))

    def handle(self, prompt):
        if m := re.search(r"take a note[:\-]?\s*(.+)", prompt, re.IGNORECASE):
            self.notes.append({"text": m.group(1).strip(), "timestamp": datetime.now().isoformat()})
            self._save()
            return "Got it. Note saved."

        if re.search(r"(show|list) notes", prompt, re.IGNORECASE):
            if not self.notes:
                return "You have no notes yet."
            return "Here are your notes:\n" + "\n".join(
                f"{i+1}. {n['text']}" for i, n in enumerate(self.notes))

        if m := re.search(r"delete note (\d+)", prompt, re.IGNORECASE):
            idx = int(m.group(1)) - 1
            if 0 <= idx < len(self.notes):
                removed = self.notes.pop(idx)
                self._save()
                return f"Deleted note: {removed['text']}"
            return "Couldn’t find that note to delete."

        return "I’m not sure what to do with that note request."

```

---

## File: `services/handlers/web_search_handler.py`

**Path:** `services/handlers/web_search_handler.py`

```
class WebSearchHandler:
    def __init__(self, web_search_service, model, system_prompt, text):
        self.web = web_search_service
        self.model = model
        self.system_prompt = system_prompt
        self.text = text

    def handle(self, prompt: str) -> str:
        import ollama

        results = self.web.search(prompt)
        if not results:
            return self.text.get("web.none")

        sources = "\n\n".join(
            f"[{i+1}] {item['title']}\n{item['snippet']}\n(Source: {item['url']})"
            for i, item in enumerate(results)
        )

        summarization_prompt = {
            "role": "user",
            "content": (
                f"{self.text.get('web.summary_prefix')}\n\n"
                f"User asked: {prompt}\n\n"
                f"[WEB RESULTS]\n{sources}\n[/WEB RESULTS]"
            )
        }

        response = ollama.chat(model=self.model, messages=[
            self.system_prompt, summarization_prompt
        ])
        return response['message']['content']

```

---

## File: `services/intent_detector.py`

**Path:** `services/intent_detector.py`

```
import re

class IntentDetector:
    def detect(self, prompt: str) -> str:
        if re.search(r"\b(remember to|update memory|remove memory|list memories)\b", prompt, re.IGNORECASE):
            return "memory"
        if re.search(r"\b(find|search|locate|where is)\b", prompt, re.IGNORECASE):
            return "file_search"
        if re.search(r"\b(search|look up|what is|who is|tell me about)\b", prompt.lower()):
            return "web_search"
        return "default"


```

---

## File: `services/kwd_service.py`

**Path:** `services/kwd_service.py`

```
import numpy as np
import logging
from collections import deque
import time

class KWDService:
    # --- Configuration ---
    RATE = 16000
    MAX_INT16 = 32767.0
    OWW_EXPECTED_SAMPLES = 16000  # openwakeword expects 1 second of audio
    COOLDOWN_SECONDS = 2.0  # Cooldown period after detection

    def __init__(self, oww_model, vad, dynamic_rms):
        self.log = logging.getLogger("KWD")
        self.oww_model = oww_model
        self.vad = vad
        self.dynamic_rms = dynamic_rms
        
        # Buffer to hold exactly 1 second of audio data for openwakeword
        self.audio_buffer = deque(maxlen=self.OWW_EXPECTED_SAMPLES)
        # Initialize with silence
        self.audio_buffer.extend(np.zeros(self.OWW_EXPECTED_SAMPLES, dtype=np.int16))
        
        # Cooldown tracking
        self.last_detection_time = 0
        self.in_cooldown = False
        
        # KWD control
        self.enabled = False  # KWD starts disabled

    def enable(self):
        """Enable wake word detection."""
        self.enabled = True
        self.log.info("Wake word detection enabled")
    
    def disable(self):
        """Disable wake word detection."""
        self.enabled = False
        self.log.info("Wake word detection disabled")
    
    def process_audio(self, audio_chunk_bytes):
        """
        Continuously processes audio chunks, feeding them into a sliding 
        1-second buffer for wake word detection.
        """
        # Skip processing if KWD is disabled
        if not self.enabled:
            return None, None
        
        # Convert raw bytes to numpy array
        chunk_np = np.frombuffer(audio_chunk_bytes, dtype=np.int16)
        
        # Add new audio to the right of the buffer, pushing out old audio from the left
        self.audio_buffer.extend(chunk_np)
        
        # Check if we're in cooldown period
        current_time = time.time()
        if self.in_cooldown:
            if current_time - self.last_detection_time < self.COOLDOWN_SECONDS:
                return None, None
            else:
                self.in_cooldown = False
                self.log.debug("Cooldown period ended")
        
        # === Audio filtering before wake word detection ===
        
        # 1. Check RMS threshold - skip if audio is too quiet (background noise)
        dynamic_threshold = self.dynamic_rms.get_threshold()
        audio_np = chunk_np.astype(np.float32) / self.MAX_INT16
        current_rms = np.sqrt(np.mean(audio_np**2))
        
        if current_rms <= dynamic_threshold:
            # Audio is below dynamic threshold, likely background noise
            return None, None
        
        # 2. Use VAD to confirm voice activity
        try:
            is_speech = self.vad.is_speech(audio_chunk_bytes, sample_rate=self.RATE)
            if not is_speech:
                # No voice activity detected
                return None, None
        except Exception as e:
            self.log.debug(f"VAD error: {e}, proceeding without VAD check")
        
        # === Proceed with wake word detection ===
        
        # Get the current 1-second window for prediction
        prediction_buffer = np.array(self.audio_buffer, dtype=np.int16)

        # Ensure the buffer is exactly the size OWW expects
        if len(prediction_buffer) != self.OWW_EXPECTED_SAMPLES:
            self.log.warning(
                f"Prediction buffer size is {len(prediction_buffer)}, expected "
                f"{self.OWW_EXPECTED_SAMPLES}. Skipping prediction."
            )
            return None, None

        try:
            # Send the 1-second buffer to the wake word model
            prediction = self.oww_model.predict(prediction_buffer)
            
            # Check if any score is above the required threshold of 0.77
            if any(score > 0.77 for score in prediction.values()):
                self.log.info(f"Wake word detected! Scores: {prediction}")
                # Enter cooldown period
                self.enter_cooldown()
                # Return the full buffer that contains the wake word
                return prediction, prediction_buffer

        except Exception as e:
            self.log.error(f"Wake word prediction failed: {e}")
        
        return None, None

    def enter_cooldown(self):
        """Enter cooldown period to prevent multiple detections from one utterance."""
        self.in_cooldown = True
        self.last_detection_time = time.time()
        self.log.debug(f"Entering cooldown for {self.COOLDOWN_SECONDS} seconds")

```

---

## File: `services/llama_file_search_service.py`

**Path:** `services/llama_file_search_service.py`

```
import os
from llama_index.core import StorageContext, load_index_from_storage
from llama_index.core.settings import Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.faiss import FaissVectorStore
from pathlib import Path

class LlamaFileSearchService:
    def __init__(self, index_path="config/faiss_index"):
        self.index_path = index_path
        self.index = None
        self._initialize_embedder()
        self._load_index()

    def _initialize_embedder(self):
        Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

    def _load_index(self):
        if not os.path.exists(self.index_path):
            print(f"[INFO] Index path {self.index_path} does not exist. Run indexing first.")
            return

        try:
            storage_context = StorageContext.from_defaults(persist_dir=self.index_path)
            self.index = load_index_from_storage(storage_context)
            print("[INFO] FAISS index loaded successfully.")
        except Exception as e:
            print(f"[ERROR] Failed to load index: {e}")
            self.index = None

    def search(self, query: str, top_k: int = 10):
        if self.index is None:
            return {
                "exact_matches": [],
                "fuzzy_matches": [],
                "content_matches": [],
                "all_results": []
            }

        try:
            # Query the index
            query_engine = self.index.as_query_engine(similarity_top_k=top_k)
            response = query_engine.query(query)
            
            # Extract file paths from source nodes
            file_paths = []
            if hasattr(response, 'source_nodes') and response.source_nodes:
                for node in response.source_nodes:
                    if hasattr(node, 'node') and hasattr(node.node, 'metadata'):
                        file_path = node.node.metadata.get('file_path', '')
                        if file_path and file_path not in file_paths:
                            file_paths.append(file_path)
            
            # For compatibility with the existing handler, classify results
            # In this vector-based approach, all results are essentially "content matches"
            return {
                "exact_matches": [],  # Vector search doesn't do exact filename matching
                "fuzzy_matches": [],  # Vector search doesn't do fuzzy filename matching  
                "content_matches": file_paths,
                "all_results": file_paths
            }
            
        except Exception as e:
            print(f"[ERROR] Search failed: {e}")
            return {
                "exact_matches": [],
                "fuzzy_matches": [],
                "content_matches": [],
                "all_results": []
            }

    def is_index_available(self):
        return self.index is not None


```

---

## File: `services/llama_indexing_service.py`

**Path:** `services/llama_indexing_service.py`

```

import os
import json
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext
from llama_index.core.settings import Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.faiss import FaissVectorStore
import faiss

class LlamaIndexingService:
    def __init__(self, config_path="config/search_config.json", index_path="config/faiss_index"):
        self.config_path = config_path
        self.index_path = index_path
        self._initialize_embedder()

    def _initialize_embedder(self):
        Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

    def _load_search_paths(self):
        try:
            with open(self.config_path, "r") as f:
                data = json.load(f)
                return [path for path in data.get("search_paths", []) if os.path.exists(path)]
        except Exception as e:
            print(f"[ERROR] Failed to load search paths: {e}")
            return []

    def build_and_save_index(self):
        search_paths = self._load_search_paths()
        if not search_paths:
            print("[INFO] No valid search paths found. Aborting indexing.")
            return

        print("[INFO] Loading documents from specified paths...")
        all_documents = []
        for path in search_paths:
            try:
                documents = SimpleDirectoryReader(input_dir=path).load_data()
                all_documents.extend(documents)
                print(f"[INFO] Loaded {len(documents)} documents from {path}")
            except Exception as e:
                print(f"[WARN] Failed to load documents from {path}: {e}")
        
        documents = all_documents
        
        if not documents:
            print("[INFO] No documents found to index.")
            return

        print(f"[INFO] Loaded {len(documents)} documents. Now creating FAISS index...")
        # Get embedding dimension by creating a dummy embedding
        dummy_embedding = Settings.embed_model.get_text_embedding("dummy query")
        d = len(dummy_embedding)

        faiss_index = faiss.IndexFlatL2(d)
        vector_store = FaissVectorStore(faiss_index=faiss_index)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        index = VectorStoreIndex.from_documents(
            documents, storage_context=storage_context
        )

        print(f"[INFO] Index created successfully. Saving to {self.index_path}...")
        index.storage_context.persist(persist_dir=self.index_path)
        print("[INFO] Indexing complete.")



```

---

## File: `services/llm_client.py`

**Path:** `services/llm_client.py`

```
#!/usr/bin/env python3
"""
HTTP client for the LLM microservice.
Provides the same interface as the original LLM service but communicates via HTTP.
"""

import requests
import time
from .logger import app_logger
from .exceptions import LLMException
from .intent_detector import IntentDetector

class LLMClient:
    """HTTP client for LLM microservice that mimics the original LLM service interface."""
    
    def __init__(self, host="127.0.0.1", port=8003, timeout=120):
        self.log = app_logger.get_logger("llm_client")
        self.base_url = f"http://{host}:{port}"
        self.timeout = timeout
        self.intent_detector = IntentDetector()  # Add intent detector
        self.log.info(f"LLM client initialized for {self.base_url}")
    
    def get_response(self, prompt):
        """Send prompt to LLM microservice for a response."""
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/chat",
                json={"prompt": prompt},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                duration = time.time() - start_time
                self.log.debug(f"LLM chat request completed in {duration:.2f}s")
                result = response.json()
                
                # Extract response and metrics
                llm_response = result.get("response", "")
                metrics = result.get("metrics", {})
                
                self.log.debug(f"LLM Client received metrics: {metrics}")
                
                # Return tuple (response, metrics) for consistency with LLMService
                return llm_response, metrics
            else:
                error_msg = f"LLM chat request failed: {response.status_code} - {response.text}"
                self.log.error(error_msg)
                raise LLMException(error_msg)
                
        except requests.exceptions.RequestException as e:
            error_msg = f"LLM service communication error: {e}"
            self.log.error(error_msg)
            raise LLMException(error_msg) from e
    
    def warmup_llm(self):
        """Send warmup request to LLM microservice."""
        try:
            response = requests.post(
                f"{self.base_url}/warmup",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                self.log.debug("LLM service warmed up successfully")
                return response.json()
            else:
                error_msg = f"LLM warmup request failed: {response.status_code} - {response.text}"
                self.log.error(error_msg)
                raise LLMException(error_msg)
                
        except requests.exceptions.RequestException as e:
            error_msg = f"LLM service communication error during warmup: {e}"
            self.log.error(error_msg)
            raise LLMException(error_msg) from e
    
    def health_check(self):
        """Check if the LLM microservice is responsive."""
        try:
            response = requests.get(f"{self.base_url}/docs", timeout=5)
            return response.status_code == 200
        except:
            return False

```

---

## File: `services/llm_service.py`

**Path:** `services/llm_service.py`

```
import ollama
import os
import time
from datetime import datetime
from .logger import app_logger
from .exceptions import LLMException, ResourceException, ConfigurationException
from .web_search_service import WebSearchService
from .llama_file_search_service import LlamaFileSearchService
from .tts_service import TTSService
from .intent_detector import IntentDetector
from .llm_text import LLMText
from .handlers.file_search_handler import FileSearchHandler
from .handlers.memory_handler import MemoryHandler
from .handlers.web_search_handler import WebSearchHandler
from .handlers.note_handler import NoteHandler


class LLMService:
    def __init__(self, model='mistral'):
        self.log = app_logger.get_logger("llm_service")
        self.log.info(f"Initializing LLM service with model: {model}")
        
        self.model = model
        self._check_gpu_availability()
        self.dialog_log_file = None

        self.text = LLMText()
        self.intent_detector = IntentDetector()
        self.tts = TTSService()
        self.web = WebSearchService()
        self.search = LlamaFileSearchService()
        self.memory_path = os.path.join("config", "memory.log")

        self.system_prompt = {'role': 'system', 'content': self._build_system_prompt()}
        self.history = [self.system_prompt]
        self._create_new_dialog_log()

        # Handlers
        self.handlers = {
            "file_search": FileSearchHandler(self.search, self.tts, self.text),
            "memory": MemoryHandler(self.memory_path, self.text),
            "web_search": WebSearchHandler(self.web, self.model, self.system_prompt, self.text),
            "note": NoteHandler(),  # NoteHandler takes a path, not LLMText object
        }

    def _check_gpu_availability(self):
        """Check if Ollama is using GPU acceleration and log the details."""
        try:
            # Check if CUDA is available on the system
            import subprocess
            try:
                result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader'], 
                                       capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    gpu_info = result.stdout.strip().split(', ')
                    gpu_name = gpu_info[0] if len(gpu_info) > 0 else "Unknown GPU"
                    gpu_memory = gpu_info[1] if len(gpu_info) > 1 else "Unknown Memory"
                    self.log.info(f"LLM (Ollama) running on GPU: {gpu_name} ({gpu_memory})")
                else:
                    self.log.warning("LLM (Ollama) GPU status unknown - nvidia-smi failed")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                self.log.warning("LLM (Ollama) running on CPU - NVIDIA GPU not detected")
        except Exception as e:
            self.log.warning(f"Could not determine LLM GPU status: {e}")

    def _build_system_prompt(self):
        """Build the system prompt with memory and personality."""
        memory_block = self._load_memory()
        personality = self._load_personality()
        return memory_block + personality

    def _load_memory(self):
        """Load long-term memories from the memory file."""
        try:
            if os.path.exists(self.memory_path):
                with open(self.memory_path, "r", encoding="utf-8") as f:
                    memories = [line.strip() for line in f if line.strip()]
                    if memories:
                        memory_lines = [f"- {m}" for m in memories]
                        return "[MEMORY]\n" + "\n".join(memory_lines) + "\n[/MEMORY]\n\n"
        except IOError as e:
            self.log.warning(f"Could not read memory file at {self.memory_path}: {e}")
        return ""

    def _load_personality(self):
        """Load the assistant's personality from a config file."""
        try:
            with open("config/system_prompt.txt", "r", encoding="utf-8") as f:
                return f.read().strip()
        except IOError as e:
            self.log.warning(f"System prompt file not found or unreadable: {e}")
            return "You are Alexa — a helpful voice assistant."

    def _create_new_dialog_log(self):
        """Create a new dialog log for the current session."""
        try:
            os.makedirs("logs", exist_ok=True)
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            self.dialog_log_file = os.path.join("logs", f"dialog_{timestamp}.log")
            self._append_to_dialog_log("SYSTEM", self.system_prompt['content'])
        except IOError as e:
            self.log.error(f"Failed to create dialog log file: {e}")
            self.dialog_log_file = None

    def _append_to_dialog_log(self, role, text):
        """Append a message to the current dialog log."""
        if not self.dialog_log_file:
            return
        try:
            timestamp = datetime.now().strftime("%d-%m-%H-%M-%S")
            with open(self.dialog_log_file, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {role}: {text.strip()}\n")
        except IOError as e:
            self.log.error(f"Failed to append to dialog log: {e}")

    def _extract_ollama_metrics(self, response):
        """Extract performance metrics from Ollama response."""
        metrics = {}
        
        try:
            # Use .get() for safe dictionary access
            total_duration = response.get('total_duration', 0)
            load_duration = response.get('load_duration', 0)
            prompt_eval_duration = response.get('prompt_eval_duration', 0)
            eval_duration = response.get('eval_duration', 0)
            prompt_eval_count = response.get('prompt_eval_count', 0)
            eval_count = response.get('eval_count', 0)

            if total_duration > 0:
                metrics['total_duration'] = f"{total_duration / 1_000_000_000:.2f}s"
            
            if load_duration > 0:
                metrics['load_duration'] = f"{load_duration / 1_000_000_000:.3f}s"
            
            if prompt_eval_duration > 0:
                prompt_eval_time = prompt_eval_duration / 1_000_000_000
                metrics['prompt_eval_duration'] = f"{prompt_eval_time:.3f}s"
                metrics['time_to_first_token'] = f"{prompt_eval_time:.3f}s"

            if eval_duration > 0:
                metrics['eval_duration'] = f"{eval_duration / 1_000_000_000:.2f}s"
                if eval_count > 0:
                    tokens_per_sec = eval_count / (eval_duration / 1_000_000_000)
                    metrics['tokens_per_second'] = f"{tokens_per_sec:.1f}"

            if prompt_eval_count > 0:
                metrics['prompt_tokens'] = prompt_eval_count
            
            if eval_count > 0:
                metrics['completion_tokens'] = eval_count
            
            self.log.debug(f"Extracted Ollama metrics: {metrics}")
            
        except Exception as e:
            self.log.warning(f"Failed to extract Ollama metrics: {e}")
        
        return metrics

    def warmup_llm(self):
        """Warm up the LLM to reduce initial response time."""
        try:
            ollama.chat(model=self.model, messages=[
                {'role': 'system', 'content': 'You are a warmup agent.'},
                {'role': 'user', 'content': 'Just say: ready'}
            ])
        except Exception as e:
            raise LLMException("LLM warmup failed", context={"error": str(e)})

    def get_response(self, prompt):
        """Get a response from the LLM, handling intents and history."""
        self.log.debug("Getting LLM response...")
        self._append_to_dialog_log("USER", prompt)

        try:
            # Intent detection
            intent = self.intent_detector.detect(prompt)
            self.log.info(f"Detected intent: {intent}")
            self._append_to_dialog_log("INTENT", intent)

            # Handle specialized intents
            if intent in self.handlers:
                start_time = time.time()
                reply = self.handlers[intent].handle(prompt)
                duration = time.time() - start_time
                app_logger.log_performance(
                    f"intent_{intent}", duration, {"input_length": len(prompt)}
                )
                self._append_to_dialog_log("ASSISTANT", reply)
                # Return tuple for consistency (reply, metrics)
                return reply, {}

            # Default: general LLM chat
            self.history.append({'role': 'user', 'content': prompt})
            
            # Ensure system prompt is always first in the messages sent to Ollama
            messages_to_send = self.history[-16:]
            if messages_to_send[0]['role'] != 'system':
                # Always include system prompt at the start
                messages_to_send = [self.system_prompt] + messages_to_send
            
            response = ollama.chat(model=self.model, messages=messages_to_send)
            reply = response['message']['content']
            self.history.append({'role': 'assistant', 'content': reply})
            self._append_to_dialog_log("ASSISTANT", reply)
            
            # Extract Ollama's native metrics
            metrics = self._extract_ollama_metrics(response)
            return reply, metrics
            
        except ollama.ResponseError as e:
            error_message = f"Ollama API error: {e.error}"
            self.log.error(error_message, extra={
                "props": {"status_code": e.status_code}
            })
            self._append_to_dialog_log("ASSISTANT_ERROR", error_message)
            return "I'm sorry, I'm having trouble connecting to my brain right now.", {}
        except Exception as e:
            error_message = f"Unexpected error in LLM service: {e}"
            self.log.critical(error_message, exc_info=True)
            self._append_to_dialog_log("ASSISTANT_ERROR", error_message)
            return f"Error: {error_message}", {}

```

---

## File: `services/llm_service_server.py`

**Path:** `services/llm_service_server.py`

```
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
    uvicorn.run(app, host="0.0.0.0", port=8003)

```

---

## File: `services/llm_streaming_client.py`

**Path:** `services/llm_streaming_client.py`

```
#!/usr/bin/env python3
"""
Enhanced LLM client with streaming capabilities for real-time response processing.
Supports both regular HTTP requests and Server-Sent Events (SSE) streaming.
"""

import requests
import time
import json
import sseclient
from typing import Iterator, Dict, Any, Optional, Callable
from .logger import app_logger
from .exceptions import LLMException
from .intent_detector import IntentDetector


class StreamingLLMClient:
    """HTTP client for LLM microservice with streaming support."""
    
    def __init__(self, host="127.0.0.1", port=8003, timeout=120):
        self.log = app_logger.get_logger("streaming_llm_client")
        self.base_url = f"http://{host}:{port}"
        self.timeout = timeout
        self.intent_detector = IntentDetector()
        self.log.info(f"Streaming LLM client initialized for {self.base_url}")
    
    def get_response(self, prompt: str) -> tuple:
        """Get a non-streaming response (backward compatibility)."""
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/chat",
                json={"prompt": prompt},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                duration = time.time() - start_time
                self.log.debug(f"LLM chat request completed in {duration:.2f}s")
                result = response.json()
                
                llm_response = result.get("response", "")
                metrics = result.get("metrics", {})
                
                return llm_response, metrics
            else:
                error_msg = f"LLM chat request failed: {response.status_code} - {response.text}"
                self.log.error(error_msg)
                raise LLMException(error_msg)
                
        except requests.exceptions.RequestException as e:
            error_msg = f"LLM service communication error: {e}"
            self.log.error(error_msg)
            raise LLMException(error_msg) from e
    
    def get_streaming_response(self, prompt: str, chunk_threshold: int = 50, 
                             sentence_boundary: bool = True) -> Iterator[Dict[str, Any]]:
        """
        Get a streaming response from the LLM service.
        
        Args:
            prompt: User input prompt
            chunk_threshold: Minimum characters before yielding chunk
            sentence_boundary: Whether to break on sentence boundaries
            
        Yields:
            Dict containing:
            - type: 'intent', 'first_token', 'chunk', 'complete', or 'error'
            - content: Text content (if applicable)
            - other fields based on type
        """
        try:
            self.log.info(f"Starting streaming request for: '{prompt[:50]}...'")
            
            response = requests.post(
                f"{self.base_url}/chat/stream",
                json={
                    "prompt": prompt,
                    "chunk_threshold": chunk_threshold,
                    "sentence_boundary": sentence_boundary
                },
                stream=True,
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                error_msg = f"Streaming request failed: {response.status_code} - {response.text}"
                self.log.error(error_msg)
                raise LLMException(error_msg)
            
            # Process Server-Sent Events
            client = sseclient.SSEClient(response)
            
            for event in client.events():
                if event.data:
                    try:
                        data = json.loads(event.data)
                        yield data
                    except json.JSONDecodeError as e:
                        self.log.warning(f"Failed to parse SSE data: {e}")
                        continue
                        
        except requests.exceptions.RequestException as e:
            error_msg = f"Streaming communication error: {e}"
            self.log.error(error_msg)
            yield {
                'type': 'error',
                'content': error_msg,
                'is_final': True
            }
    
    def get_streaming_text(self, prompt: str, **kwargs) -> Iterator[str]:
        """
        Simplified streaming interface that yields only text chunks.
        Perfect for TTS integration.
        """
        for chunk_data in self.get_streaming_response(prompt, **kwargs):
            if chunk_data.get('type') == 'chunk' and chunk_data.get('content'):
                yield chunk_data['content']
            elif chunk_data.get('type') == 'complete' and chunk_data.get('content'):
                # Yield the complete response if no chunks were sent
                content = chunk_data['content']
                if content:
                    yield content
    
    def warmup_llm(self):
        """Send warmup request to LLM microservice."""
        try:
            response = requests.post(
                f"{self.base_url}/warmup",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                self.log.debug("LLM service warmed up successfully")
                return response.json()
            else:
                error_msg = f"LLM warmup request failed: {response.status_code} - {response.text}"
                self.log.error(error_msg)
                raise LLMException(error_msg)
                
        except requests.exceptions.RequestException as e:
            error_msg = f"LLM service communication error during warmup: {e}"
            self.log.error(error_msg)
            raise LLMException(error_msg) from e
    
    def health_check(self):
        """Check if the LLM microservice is responsive."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                result = response.json()
                return result.get("status") == "healthy"
            return False
        except:
            return False


class StreamingTTSIntegration:
    """
    Integration class for streaming LLM responses directly to TTS.
    Provides minimal latency between LLM generation and TTS playback.
    """
    
    def __init__(self, llm_client: StreamingLLMClient, tts_service, 
                 min_chunk_size: int = 100, log=None):
        self.llm_client = llm_client
        self.tts_service = tts_service
        self.min_chunk_size = min_chunk_size
        self.log = log or app_logger.get_logger("streaming_tts_integration")
    
    def speak_streaming_response(self, prompt: str, 
                               chunk_callback: Optional[Callable[[str], None]] = None) -> str:
        """
        Generate streaming LLM response and immediately send chunks to TTS.
        
        Args:
            prompt: User input
            chunk_callback: Optional callback function for each chunk (for debugging/logging)
            
        Returns:
            Complete response text
        """
        self.log.info(f"Starting streaming TTS for: '{prompt[:50]}...'")
        
        buffer = ""
        complete_response = ""
        chunks_sent = 0
        first_chunk_time = None
        start_time = time.time()
        
        try:
            for chunk_data in self.llm_client.get_streaming_response(prompt):
                chunk_type = chunk_data.get('type')
                
                if chunk_type == 'first_token':
                    first_token_time = chunk_data.get('time', 0)
                    self.log.info(f"First token received in {first_token_time:.3f}s")
                
                elif chunk_type == 'chunk':
                    content = chunk_data.get('content', '')
                    if content:
                        buffer += content
                        complete_response += content
                        
                        # Send to TTS when buffer is large enough
                        if len(buffer) >= self.min_chunk_size:
                            if first_chunk_time is None:
                                first_chunk_time = time.time()
                                self.log.info("Starting TTS playback with first chunk")
                            
                            # Send chunk to TTS
                            self.tts_service.speak(buffer.strip())
                            chunks_sent += 1
                            
                            if chunk_callback:
                                chunk_callback(buffer)
                            
                            self.log.debug(f"Sent chunk {chunks_sent} to TTS: {len(buffer)} chars")
                            buffer = ""
                
                elif chunk_type == 'complete':
                    # Handle any remaining content
                    if buffer.strip():
                        self.tts_service.speak(buffer.strip())
                        chunks_sent += 1
                        
                        if chunk_callback:
                            chunk_callback(buffer)
                    
                    # Log final metrics
                    metrics = chunk_data.get('metrics', {})
                    total_time = time.time() - start_time
                    
                    self.log.info(f"Streaming TTS completed:")
                    self.log.info(f"  Total time: {total_time:.2f}s")
                    self.log.info(f"  Response length: {len(complete_response)} chars")
                    self.log.info(f"  Chunks sent to TTS: {chunks_sent}")
                    self.log.info(f"  LLM metrics: {metrics}")
                    
                    break
                
                elif chunk_type == 'error':
                    error_msg = chunk_data.get('content', 'Unknown error')
                    self.log.error(f"Streaming error: {error_msg}")
                    
                    # Try to speak whatever we have
                    if buffer.strip():
                        self.tts_service.speak(buffer.strip())
                    
                    return complete_response
            
            return complete_response
            
        except Exception as e:
            self.log.error(f"Error in streaming TTS integration: {e}")
            # Fallback: speak whatever we have
            if buffer.strip():
                self.tts_service.speak(buffer.strip())
            return complete_response


def create_streaming_integration(host="127.0.0.1", port=8003):
    """
    Factory function to create streaming LLM client and TTS integration.
    """
    from .tts_service import TTSService
    
    llm_client = StreamingLLMClient(host=host, port=port)
    tts_service = TTSService()
    
    integration = StreamingTTSIntegration(llm_client, tts_service)
    
    return llm_client, tts_service, integration


# Usage example
if __name__ == "__main__":
    # Demo streaming functionality
    client = StreamingLLMClient()
    
    print("🚀 Testing streaming LLM client...")
    
    prompt = "Tell me a short story about artificial intelligence"
    print(f"Prompt: {prompt}\n")
    
    for chunk_data in client.get_streaming_response(prompt):
        chunk_type = chunk_data.get('type')
        
        if chunk_type == 'intent':
            print(f"[Intent] {chunk_data.get('content')}")
        elif chunk_type == 'first_token':
            print(f"[First Token] {chunk_data.get('time'):.3f}s")
        elif chunk_type == 'chunk':
            print(chunk_data.get('content', ''), end='', flush=True)
        elif chunk_type == 'complete':
            print(f"\n\n[Complete] Metrics: {chunk_data.get('metrics')}")
        elif chunk_type == 'error':
            print(f"\n[Error] {chunk_data.get('content')}")

```

---

## File: `services/llm_streaming_server.py`

**Path:** `services/llm_streaming_server.py`

```
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
from services.logger import app_logger

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
        llm_service = LLMService(model='alexa-4k')  # Use optimized 4K model
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

```

---

## File: `services/llm_text.py`

**Path:** `services/llm_text.py`

```
import json
import os

class LLMText:
    def __init__(self, config_path="config/llm_responses.json"):
        self.data = {}
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                self.data = json.load(f)

    def get(self, key, default=""):
        return self.data.get(key, default)

    def format(self, key, **kwargs):
        template = self.get(key)
        return template.format(**kwargs) if template else ""

```

---

## File: `services/loader.py`

**Path:** `services/loader.py`

```
import torch
import webrtcvad
import numpy as np
import os
import time
from openwakeword.model import Model
from .stt_service import STTService
from .llm_service import LLMService
from .tts_client import TTSClient
from .dynamic_rms_service import DynamicRMSService
from .service_manager import ServiceManager
from .logger import app_logger
from .exceptions import ServiceInitializationException, ResourceException

def load_services():
    """Load all voice assistant services with comprehensive error handling."""
    log = app_logger.get_logger("loader")
    services = {}
    
    try:
        # Initialize VAD
        log.info("Initializing Voice Activity Detection...")
        vad = webrtcvad.Vad(1)
        services["vad"] = vad
        
        # Load wake word model
        log.info("Loading wake word detection model...")
        model_paths = [os.path.join("models", "alexa_v0.1.onnx")]
        
        # Verify model files exist
        for model_path in model_paths:
            if not os.path.exists(model_path):
                raise ResourceException(
                    f"Wake word model not found: {model_path}",
                    context={"model_path": model_path}
                )
        
        oww_model = Model(wakeword_model_paths=model_paths)
        services["oww_model"] = oww_model
        
        # Initialize core services
        try:
            log.info("Initializing Speech-to-Text service...")
            stt_service = STTService()
            services["stt_service"] = stt_service
        except Exception as e:
            raise ServiceInitializationException("STT", str(e))
        
        try:
            log.info("Initializing Language Model service...")
            llm_service = LLMService(model='llama3.1:8b-instruct-q4_K_M')
            services["llm_service"] = llm_service
        except Exception as e:
            raise ServiceInitializationException("LLM", str(e))
        
        try:
            log.info("Initializing Text-to-Speech service...")
            tts_service = TTSService()
            services["tts_service"] = tts_service
        except Exception as e:
            raise ServiceInitializationException("TTS", str(e))
        
        try:
            log.info("Initializing Dynamic RMS service...")
            dynamic_rms = DynamicRMSService()
            dynamic_rms.start()
            services["dynamic_rms"] = dynamic_rms
        except Exception as e:
            raise ServiceInitializationException("DynamicRMS", str(e))
        
        # Warm up models for better performance
        log.info("Warming up models for optimal performance...")
        _warmup_models(oww_model, stt_service, tts_service, llm_service, log)
        
        log.info("All services loaded and warmed up successfully")
        
        return vad, oww_model, stt_service, llm_service, tts_service, dynamic_rms
        
    except (ServiceInitializationException, ResourceException) as e:
        # Cleanup any partially initialized services
        _cleanup_services(services)
        
        # Re-raise the specific exception
        raise e
    except Exception as e:
        # Cleanup any partially initialized services
        _cleanup_services(services)
        
        # Wrap unexpected errors in ServiceInitializationException
        raise ServiceInitializationException(
            "service_loader",
            f"An unexpected error occurred during service loading: {str(e)}",
            context={
                "loaded_services": list(services.keys()),
                "error_type": type(e).__name__
            }
        ) from e


def _warmup_models(oww_model, stt_service, tts_service, llm_service, log):
    """Warm up all models with detailed timing and error handling."""
    warmup_times = {}
    
    # Warm up OpenWakeWord
    try:
        log.debug("Warming up OpenWakeWord model...")
        start_time = time.time()
        oww_chunk_samples = 1280
        silent_oww_chunk = np.zeros(oww_chunk_samples, dtype=np.int16)
        oww_model.predict(silent_oww_chunk)
        warmup_times["oww"] = time.time() - start_time
        log.debug(f"OpenWakeWord warmup completed in {warmup_times['oww']:.2f}s")
    except Exception as e:
        log.warning(f"OpenWakeWord warmup failed: {e}")
    
    # Warm up Whisper STT
    try:
        log.debug(f"Warming up Whisper STT model (device: {stt_service.device})...")
        start_time = time.time()
        if stt_service.device == 'cuda':
            rate = 16000
            silent_whisper_chunk = np.zeros(rate, dtype=np.float32)
            stt_service.model.transcribe(silent_whisper_chunk, fp16=True)
        warmup_times["stt"] = time.time() - start_time
        log.debug(f"Whisper STT warmup completed in {warmup_times['stt']:.2f}s")
    except Exception as e:
        log.warning(f"Whisper STT warmup failed: {e}")
    
    # Warm up TTS
    try:
        log.debug("Warming up TTS service...")
        start_time = time.time()
        tts_service.warmup()
        warmup_times["tts"] = time.time() - start_time
        log.debug(f"TTS warmup completed in {warmup_times['tts']:.2f}s")
    except Exception as e:
        log.warning(f"TTS warmup failed: {e}")
    
    # Warm up LLM
    try:
        log.debug("Warming up Language Model...")
        start_time = time.time()
        llm_service.warmup_llm()
        warmup_times["llm"] = time.time() - start_time
        log.debug(f"LLM warmup completed in {warmup_times['llm']:.2f}s")
    except Exception as e:
        log.warning(f"LLM warmup failed: {e}")
    
    # Log performance metrics
    total_warmup_time = sum(warmup_times.values())
    app_logger.log_performance(
        "model_warmup",
        total_warmup_time,
        warmup_times
    )
    
    log.info(f"Model warmup completed in {total_warmup_time:.2f} seconds")


def _cleanup_services(services):
    """Clean up partially initialized services."""
    log = app_logger.get_logger("loader")
    
    for service_name, service in services.items():
        try:
            if service_name == "dynamic_rms" and hasattr(service, 'stop'):
                service.stop()
                log.debug(f"Cleaned up {service_name}")
        except Exception as e:
            log.warning(f"Error cleaning up {service_name}: {e}")

```

---

## File: `services/logger.py`

**Path:** `services/logger.py`

```
import logging
import logging.config
import os
import sys
import json
import traceback
from datetime import datetime

# ---
# Filter to remove ANSI color codes from log records
# ---
class ColorFilter(logging.Filter):
    def filter(self, record):
        # Remove ANSI color codes from all string fields
        import re
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        
        record.levelname = ansi_escape.sub('', record.levelname).strip()
        record.name = ansi_escape.sub('', record.name).strip()
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            record.msg = ansi_escape.sub('', record.msg)
        return True

# ---
# Custom formatter for structured JSON logging
# ---
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, 'props'):
            log_record.update(record.props)
        return json.dumps(log_record)

# ---
# Custom formatter for colored console output
# ---
class ColorFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": "\033[94m",    # Blue
        "INFO": "\033[92m",     # Green
        "WARNING": "\033[93m", # Yellow
        "ERROR": "\033[91m",    # Red
        "CRITICAL": "\033[95m",# Magenta
        "RESET": "\033[0m",
    }

    def format(self, record):
        color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
        record.levelname = f"{color}{record.levelname.ljust(8)}{self.COLORS['RESET']}"
        record.name = f"\033[96m{record.name.ljust(20)}\033[0m" # Cyan, aligned to microservices_loader
        return super().format(record)


class AppLogger:
    _instance = None
    _loggers = {}

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(AppLogger, cls).__new__(cls)
        return cls._instance

    def __init__(self, log_dir="logs", console_level=logging.INFO, file_level=logging.DEBUG):
        if hasattr(self, '_initialized') and self._initialized:
            return
        self._initialized = True
        
        self.log_dir = log_dir
        self.console_level = console_level
        self.file_level = file_level
        self.log_file = os.path.join(self.log_dir, "app.jsonl")

        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir, exist_ok=True)

        # Performance timers log
        self.perf_log_file = os.path.join(self.log_dir, "performance.jsonl")

    def get_logger(self, name="main"):
        if name in self._loggers:
            return self._loggers[name]

        logger = logging.getLogger(name)
        logger.setLevel(self.file_level)
        logger.propagate = False

        if not logger.handlers:
            # Console handler with colors
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self.console_level)
            console_format = ColorFormatter("%(name)s - %(levelname)s - %(message)s")
            console_handler.setFormatter(console_format)
            logger.addHandler(console_handler)

            # JSON file handler (no colors)
            file_handler = logging.FileHandler(self.log_file)
            file_handler.setLevel(self.file_level)
            file_handler.addFilter(ColorFilter())  # Remove color codes from file logs
            file_handler.setFormatter(JsonFormatter())
            logger.addHandler(file_handler)

        self._loggers[name] = logger
        return logger

    def handle_exception(self, exc_type, exc_value, exc_traceback, logger_name="main", context=None):
        logger = self.get_logger(logger_name)
        
        # Construct structured log context
        props = {
            "exception_type": exc_type.__name__,
            "traceback": ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback)),
            "context": context or {},
        }

        # Log the critical error
        logger.critical(f"{exc_value}", extra={"props": props})

        # Also log to console for immediate visibility during development
        print(f"\nCRITICAL ERROR: {exc_value}\nTraceback:\n{''.join(traceback.format_tb(exc_traceback))}", file=sys.stderr)

    def log_performance(self, event: str, duration: float, context: dict = None):
        perf_record = {
            "timestamp": datetime.now().isoformat(),
            "event": event,
            "duration_ms": round(duration * 1000, 2),
            "context": context or {}
        }
        with open(self.perf_log_file, 'a') as f:
            f.write(json.dumps(perf_record) + '\n')

# ---
# Singleton instance of the logger
# ---
app_logger = AppLogger()

# ---
# Backward compatibility function
# ---
def setup_logging(log_file=None, log_level=logging.INFO):
    """
    Backward compatibility function for existing code.
    Returns the main logger from the new system.
    """
    return app_logger.get_logger("main")

```

---

## File: `services/memory_logger.py`

**Path:** `services/memory_logger.py`

```
# services/memory_logger.py
import subprocess
import threading
import time
import os
import psutil
from datetime import datetime
from .logger import app_logger
# Dashboard integration removed - using new DashboardService

class MemoryLogger:
    TARGET_PROCESSES = ["python", "ollama", "openwakeword"]

    def __init__(self, log_file=os.path.join('logs', 'memory.csv'), interval=1):
        self.log = app_logger.get_logger("memory_logger")
        self.log_file = log_file
        self.interval = interval
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._log_metrics, daemon=True)

        log_dir = os.path.dirname(self.log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        if os.path.exists(self.log_file):
            os.remove(self.log_file)

    def _get_gpu_vram_by_name(self, name):
        try:
            result = subprocess.run(
                "nvidia-smi pmon -c 1",
                shell=True, capture_output=True, text=True
            )
            lines = result.stdout.strip().splitlines()
            matching = [int(line.split()[4]) for line in lines if name in line]
            return sum(matching)
        except Exception:
            return 0

    def _get_total_gpu(self):
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=memory.used,memory.total', '--format=csv,noheader,nounits'],
                capture_output=True, text=True, check=True
            )
            used, total = result.stdout.strip().split(', ')
            return int(used), int(total)
        except Exception:
            return 0, 0

    def _get_process_stats(self):
        stats = {name: {"ram": 0, "cpu": 0} for name in self.TARGET_PROCESSES}
        for proc in psutil.process_iter(['name', 'memory_info', 'cpu_percent']):
            try:
                name = proc.info['name']
                if name:
                    for target in self.TARGET_PROCESSES:
                        if target in name.lower():
                            stats[target]["ram"] += proc.memory_info().rss // (1024 * 1024)
                            stats[target]["cpu"] += proc.cpu_percent(interval=None)
            except Exception:
                continue
        return stats

    def _log_metrics(self):
        with open(self.log_file, 'w') as f:
            f.write("Time, GPU_Used, GPU_Total, GPU_Python, GPU_Ollama, GPU_OWW, "
                    "RAM_Python, RAM_Ollama, RAM_OWW, CPU_Python, CPU_Ollama, CPU_OWW\n")

            while not self._stop_event.is_set():
                now = datetime.now().strftime('%m-%d %H:%M:%S')
                gpu_used, gpu_total = self._get_total_gpu()
                gpu_python = self._get_gpu_vram_by_name("python")
                gpu_ollama = self._get_gpu_vram_by_name("ollama")
                gpu_oww = self._get_gpu_vram_by_name("openwakeword")

                proc_stats = self._get_process_stats()

                f.write(f"{now}, {gpu_used}, {gpu_total}, {gpu_python}, {gpu_ollama}, {gpu_oww}, "
                        f"{proc_stats['python']['ram']}, {proc_stats['ollama']['ram']}, {proc_stats['openwakeword']['ram']}, "
                        f"{proc_stats['python']['cpu']:.1f}, {proc_stats['ollama']['cpu']:.1f}, {proc_stats['openwakeword']['cpu']:.1f}\n")
                f.flush()

                # Dashboard integration handled by main dashboard service

                time.sleep(self.interval)

    def start(self):
        self.log.info("VRAM and system monitoring started")
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        self._thread.join()
        self.log.info("VRAM and system monitoring stopped")

```

---

## File: `services/microservices_loader.py`

**Path:** `services/microservices_loader.py`

```
import torch
import webrtcvad
import numpy as np
import os
import time
import requests
from openwakeword.model import Model
from .stt_client import STTClient
from .llm_streaming_client import StreamingLLMClient
from .tts_client import TTSClient
from .dynamic_rms_service import DynamicRMSService
from .service_manager import ServiceManager
from .logger import app_logger
from .exceptions import ServiceInitializationException, ResourceException

def load_services_microservices():
    """Load voice assistant services using microservices architecture."""
    log = app_logger.get_logger("microservices_loader")
    service_manager = ServiceManager()
    services = {}
    
    try:
        log.debug("Starting microservices-based voice assistant...")
        
        # Initialize VAD (runs locally for low latency)
        log.info("Initializing VAD...")
        vad = webrtcvad.Vad(1)
        services["vad"] = vad
        
        # Load wake word model (runs locally for low latency)
        log.info("Loading KWD model...")
        model_paths = [os.path.join("models", "alexa_v0.1.onnx")]
        
        # Verify model files exist
        for model_path in model_paths:
            if not os.path.exists(model_path):
                raise ResourceException(
                    f"Wake word model not found: {model_path}",
                    context={"model_path": model_path}
                )
        
        oww_model = Model(wakeword_model_paths=model_paths)
        services["oww_model"] = oww_model
        
        # Start all microservices
        microservices = [
            ("tts_service", "services.tts_service_server:app", 8001),
            ("stt_service", "services.stt_service_server:app", 8002),
            ("llm_service", "services.llm_streaming_server:app", 8003)
        ]
        
        for service_name, app_path, port in microservices:
            log.debug(f"Starting {service_name} microservice...")
            process = service_manager.start_service(
                service_name,
                f"python3 -m uvicorn {app_path} --host 0.0.0.0 --port {port}",
                port=port
            )
            
            if not process:
                raise ServiceInitializationException(service_name, f"Failed to start {service_name} microservice")
        
        # Initialize Dynamic RMS service (runs locally)
        try:
            log.debug("Initializing Dynamic RMS service...")
            dynamic_rms = DynamicRMSService()
            dynamic_rms.start()
            services["dynamic_rms"] = dynamic_rms
        except Exception as e:
            raise ServiceInitializationException("DynamicRMS", str(e))
        
        # Create clients for microservices and wait for them to be ready
        log.debug("Initializing microservice clients...")
        
        # TTS Client
        tts_service = TTSClient(port=8001)
        for attempt in range(30):
            if tts_service.health_check():
                log.debug("TTS microservice is ready")
                break
            time.sleep(1)
        else:
            raise ServiceInitializationException("TTS", "TTS microservice failed to become ready")
        services["tts_service"] = tts_service
        
        # STT Client
        stt_service = STTClient(port=8002, dynamic_rms=dynamic_rms)
        for attempt in range(30):
            if stt_service.health_check():
                log.debug("STT microservice is ready")
                break
            time.sleep(1)
        else:
            raise ServiceInitializationException("STT", "STT microservice failed to become ready")
        services["stt_service"] = stt_service
        
        # LLM Client
        llm_service = StreamingLLMClient(port=8003)
        for attempt in range(30):
            if llm_service.health_check():
                log.debug("LLM microservice is ready")
                break
            time.sleep(1)
        else:
            raise ServiceInitializationException("LLM", "LLM microservice failed to become ready")
        services["llm_service"] = llm_service
        
        # Warm up models
        log.debug("Warming up models for optimal performance...")
        _warmup_models_microservices(oww_model, stt_service, tts_service, llm_service, log)
        
        log.info("All services loaded and warmed up successfully")
        
        return vad, oww_model, stt_service, llm_service, tts_service, dynamic_rms, service_manager
        
    except Exception as e:
        log.error(f"Failed to load microservices: {e}", exc_info=True)
        # Cleanup
        service_manager.stop_all_services()
        _cleanup_services(services)
        raise

def _warmup_models_microservices(oww_model, stt_service, tts_service, llm_service, log):
    """Warm up all models with detailed timing and error handling."""
    warmup_times = {}
    
    # Warm up OpenWakeWord (runs locally)
    try:
        log.debug("Warming up OpenWakeWord model...")
        start_time = time.time()
        oww_chunk_samples = 1280
        silent_oww_chunk = np.zeros(oww_chunk_samples, dtype=np.int16)
        oww_model.predict(silent_oww_chunk)
        warmup_times["oww"] = time.time() - start_time
        log.debug(f"OpenWakeWord warmup completed in {warmup_times['oww']:.2f}s")
    except Exception as e:
        log.warning(f"OpenWakeWord warmup failed: {e}")
    
    # Warm up TTS microservice
    try:
        log.debug("Warming up TTS microservice...")
        start_time = time.time()
        tts_service.warmup()
        warmup_times["tts"] = time.time() - start_time
        log.debug(f"TTS microservice warmup completed in {warmup_times['tts']:.2f}s")
    except Exception as e:
        log.warning(f"TTS microservice warmup failed: {e}")
    
    # Warm up LLM microservice
    try:
        log.debug("Warming up LLM microservice...")
        start_time = time.time()
        llm_service.warmup_llm()
        warmup_times["llm"] = time.time() - start_time
        log.debug(f"LLM microservice warmup completed in {warmup_times['llm']:.2f}s")
    except Exception as e:
        log.warning(f"LLM microservice warmup failed: {e}")
    
    # Note: STT microservice warmup happens during service initialization
    # No additional warmup needed for STT client
    
    # Log performance metrics
    total_warmup_time = sum(warmup_times.values())
    app_logger.log_performance(
        "microservices_warmup",
        total_warmup_time,
        warmup_times
    )
    
    log.debug(f"Model warmup completed in {total_warmup_time:.2f} seconds")

def _cleanup_services(services):
    """Clean up partially initialized services."""
    log = app_logger.get_logger("microservices_loader")
    
    for service_name, service in services.items():
        try:
            if service_name == "dynamic_rms" and hasattr(service, 'stop'):
                service.stop()
                log.debug(f"Cleaned up {service_name}")
        except Exception as e:
            log.warning(f"Error cleaning up {service_name}: {e}")

```

---

## File: `services/service_manager.py`

**Path:** `services/service_manager.py`

```
#!/usr/bin/env python3
"""
Manages the lifecycle of all microservices, including starting,
stopping, and monitoring their health.
"""

import subprocess
import time
import atexit
from .logger import app_logger

class ServiceManager:
    def __init__(self):
        self.log = app_logger.get_logger("service_manager")
        self.services = []
        atexit.register(self.stop_all_services)

    def start_service(self, name, command, host="127.0.0.1", port=8000):
        """Start a microservice as a subprocess."""
        self.log.debug(f"Starting service: {name} on {host}:{port}")
        try:
            # Get the project root directory (parent of services directory)
            import os
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            
            process = subprocess.Popen(
                command, 
                shell=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True,
                cwd=project_root
            )
            self.services.append({
                "name": name,
                "process": process,
                "host": host,
                "port": port,
                "command": command
            })
            self.log.debug(f"Service '{name}' started with PID: {process.pid}")
            return process
        except Exception as e:
            self.log.error(f"Failed to start service '{name}': {e}", exc_info=True)
            return None

    def stop_service(self, name):
        """Stop a specific microservice by name."""
        for service in self.services:
            if service["name"] == name:
                self.log.debug(f"Stopping service: {name} (PID: {service['process'].pid})")
                service['process'].terminate()
                service['process'].wait()
                self.log.debug(f"Service '{name}' stopped")
                self.services.remove(service)
                break

    def stop_all_services(self):
        """Stop all running microservices."""
        self.log.debug("Stopping all services...")
        for service in self.services:
            self.log.debug(f"Stopping service: {service['name']} (PID: {service['process'].pid})")
            service['process'].terminate()
            service['process'].wait()
        self.log.debug("All services stopped")

    def check_service_health(self, name):
        """Check if a service is running and responsive."""
        # TODO: Implement health check logic (e.g., HTTP request)
        pass


```

---

## File: `services/stt_client.py`

**Path:** `services/stt_client.py`

```
#!/usr/bin/env python3
"""
HTTP client for the STT microservice.
Provides the same interface as the original STT service but communicates via HTTP.
"""

import requests
import time
import io
from .logger import app_logger
from .exceptions import STTException

class STTClient:
    """HTTP client for STT microservice that mimics the original STT service interface."""
    
    def __init__(self, host="127.0.0.1", port=8002, timeout=60, dynamic_rms=None):
        self.log = app_logger.get_logger("stt_client")
        self.base_url = f"http://{host}:{port}"
        self.timeout = timeout
        self.dynamic_rms = dynamic_rms
        self.log.debug(f"STT client initialized for {self.base_url}")
    
    def listen_and_transcribe(self, timeout_ms=3000):
        """Deprecated: This method creates audio conflicts. Use transcribe_audio_bytes instead."""
        self.log.error("listen_and_transcribe() creates PyAudio conflicts in microservices architecture")
        raise STTException("listen_and_transcribe() is not supported in microservices mode. Use transcribe_audio_bytes() instead.")
    
    def transcribe_audio_bytes(self, audio_data):
        """Send pre-recorded audio data to STT microservice for transcription."""
        try:
            if not audio_data:
                return ""
                
            start_time = time.time()
            transcription = self._send_for_transcription(audio_data)
            
            duration = time.time() - start_time
            app_logger.log_performance("stt_client_transcription", duration, {
                "audio_duration_ms": len(audio_data) * 1000 // (16000 * 2),  # 16kHz * 2 bytes per sample
                "transcription_length": len(transcription)
            })
            
            return transcription
            
        except Exception as e:
            error_msg = f"STT client error during transcribe_audio_bytes: {e}"
            self.log.error(error_msg)
            raise STTException(error_msg) from e
    
    def _send_for_transcription(self, audio_data):
        """Send audio data to STT microservice for transcription."""
        try:
            # Create file-like object from audio data
            audio_file = io.BytesIO(audio_data)
            
            response = requests.post(
                f"{self.base_url}/transcribe",
                files={"audio": ("audio.raw", audio_file, "application/octet-stream")},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                transcription = result.get("transcription", "")
                self.log.debug(f"STT transcription completed: '{transcription}'")
                return transcription
            else:
                error_msg = f"STT transcribe request failed: {response.status_code} - {response.text}"
                self.log.error(error_msg)
                raise STTException(error_msg)
                
        except requests.exceptions.RequestException as e:
            error_msg = f"STT service communication error: {e}"
            self.log.error(error_msg)
            raise STTException(error_msg) from e
    
    
    def health_check(self):
        """Check if the STT microservice is responsive."""
        try:
            response = requests.get(f"{self.base_url}/docs", timeout=5)
            return response.status_code == 200
        except:
            return False

```

---

## File: `services/stt_service.py`

**Path:** `services/stt_service.py`

```
import torch
import whisper
import pyaudio
import webrtcvad
import numpy as np
import os
import time
import logging.handlers
from datetime import datetime
from contextlib import contextmanager
from .logger import app_logger
from .exceptions import STTException, AudioException, ResourceException, VoiceAssistantException

# --- Configuration ---
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
VAD_FRAME_MS = 30
VAD_FRAME_SAMPLES = int(RATE * (VAD_FRAME_MS / 1000.0))
MAX_INT16 = 32767.0

class STTService:
    """A service for transcribing speech with Whisper, VAD, and dynamic thresholding."""

    def __init__(self, model_size="small.en", dynamic_rms=None):
        self.log = app_logger.get_logger("stt_service")
        self.log.info(f"Initializing STT service with model: {model_size}")
        
        self.device = self._get_device()
        self.model = self._load_model(model_size)
        self.vad = webrtcvad.Vad(3)
        self.model_size = model_size  # Store model size for transcription options
        self.dynamic_rms = dynamic_rms

        # Dedicated logger for transcriptions
        self.transcription_logger = self._setup_transcription_logger()

    def _get_device(self):
        """Determine the compute device (CUDA or CPU)."""
        if torch.cuda.is_available():
            try:
                gpu_name = torch.cuda.get_device_name(0)
                gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)  # GB
                self.log.info(f"STT (Whisper) running on GPU: {gpu_name} ({gpu_memory:.1f}GB)")
                return "cuda"
            except Exception as e:
                self.log.warning(f"CUDA is available but failed to initialize: {e}")
                self.log.warning("STT (Whisper) falling back to CPU")
                return "cpu"
        else:
            self.log.warning("STT (Whisper) running on CPU - GPU acceleration not available")
            return "cpu"

    def _load_model(self, model_size):
        """Load the Whisper ASR model with error handling."""
        try:
            self.log.info(f"Loading Whisper model: {model_size}")
            model = whisper.load_model(model_size, device=self.device)
            self.log.info("Whisper model loaded successfully")
            return model
        except Exception as e:
            raise ResourceException(
                f"Failed to load Whisper model: {model_size}",
                context={"device": self.device, "error": str(e)}
            )

    def _setup_transcription_logger(self):
        """Set up a dedicated logger for STT transcriptions."""
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        
        logger = app_logger.get_logger("transcriptions")
        logger.propagate = False # Prevent double logging
        
        # Remove default handlers if any
        if logger.hasHandlers():
            logger.handlers.clear()
            
        # Create a file handler that rotates daily
        handler = logging.handlers.TimedRotatingFileHandler(
            os.path.join(log_dir, "transcriptions.log"), 
            when='D', interval=1, backupCount=7
        )
        handler.setFormatter(logging.Formatter("%(asctime)s: %(message)s"))
        logger.addHandler(handler)
        
        return logger

    def _write_transcription_to_log(self, text):
        """Save the transcription to a dedicated rotating log file."""
        try:
            self.transcription_logger.info(text)
        except Exception as e:
            self.log.error(f"Failed to write transcription to log: {e}")

    def listen_and_transcribe(self, timeout_ms=3000):
        """Listen for audio, record until silence, and transcribe with robust error handling."""
        try:
            with self._audio_stream_manager() as stream:
                self.log.debug("Listening for command...")
                
                recorded_frames = self._record_audio(stream, timeout_ms)
                audio_data = b''.join(recorded_frames)
                
                self.log.info("Transcription started")
                start_time = time.time()
                
                transcription = self._transcribe_audio(audio_data)
                
                duration = time.time() - start_time
                app_logger.log_performance("stt_transcription", duration, {
                    "audio_duration_ms": len(audio_data) * 1000 // (RATE * 2), # 16-bit
                    "transcription_length": len(transcription)
                })
                
                if transcription:
                    self._write_transcription_to_log(transcription)
                
                return transcription
                
        except VoiceAssistantException:
            raise # Propagate known exceptions
        except Exception as e:
            raise STTException(
                f"An unexpected error occurred during transcription: {e}",
                context={"error_type": type(e).__name__}
            ) from e

    @contextmanager
    def _audio_stream_manager(self):
        """Context manager for PyAudio stream."""
        pa = pyaudio.PyAudio()
        stream = None
        try:
            stream = pa.open(
                format=FORMAT, channels=CHANNELS, rate=RATE, 
                input=True, frames_per_buffer=VAD_FRAME_SAMPLES
            )
            yield stream
        except OSError as e:
            raise AudioException(
                f"Could not open microphone stream: {e}", 
                recoverable=False
            )
        finally:
            if stream and stream.is_active():
                stream.stop_stream()
                stream.close()
            pa.terminate()

    def _record_audio(self, stream, timeout_ms):
        """Record audio from the stream until silence is detected."""
        recorded_frames = []
        silence_duration_ms = 0
        threshold = self.dynamic_rms.get_threshold() if self.dynamic_rms else 0.15
        
        self.log.debug(f"Using VAD threshold: {threshold:.2f}")

        while True:
            try:
                audio_chunk = stream.read(VAD_FRAME_SAMPLES, exception_on_overflow=False)
                recorded_frames.append(audio_chunk)

                chunk_np = np.frombuffer(audio_chunk, dtype=np.int16)
                normalized_chunk = chunk_np.astype(np.float32) / MAX_INT16
                rms = np.sqrt(np.mean(normalized_chunk**2))
                is_speech = self.vad.is_speech(audio_chunk, sample_rate=RATE) and (rms > threshold)

                if is_speech:
                    if self.dynamic_rms:
                        self.dynamic_rms.lock()
                    silence_duration_ms = 0
                else:
                    silence_duration_ms += VAD_FRAME_MS
                    if silence_duration_ms >= timeout_ms:
                        self.log.debug("Silence detected, processing audio")
                        break
            except IOError as e:
                raise AudioException(f"Error reading from audio stream: {e}")

        return recorded_frames

    def _transcribe_audio(self, audio_data):
        """Transcribe the collected audio data using Whisper."""
        audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / MAX_INT16
        
        if len(audio_np) < RATE * 0.5: # 0.5s minimum
            self.log.warning("Recording is too short, skipping transcription")
            if self.dynamic_rms:
                self.dynamic_rms.reset()
            return ""

        try:
            # Use optimized transcription settings based on model type
            transcribe_options = {
                'fp16': (self.device == "cuda"),
                'task': 'transcribe',
                'no_speech_threshold': 0.6
            }
            
            # Only add language parameter for non-English models
            if not self.model_size.endswith('.en'):
                transcribe_options['language'] = 'en'
                
            result = self.model.transcribe(audio_np, **transcribe_options)
            transcription = result['text'].strip()
            
            if self.dynamic_rms:
                self.dynamic_rms.reset()
                
            return transcription
            
        except Exception as e:
            raise STTException(
                f"Whisper model failed to transcribe audio: {e}",
                context={"audio_length_s": len(audio_np) / RATE}
            )
    
    def transcribe_audio_bytes(self, audio_bytes):
        """Transcribe audio from raw bytes (for microservice API)."""
        try:
            # Convert bytes to numpy array
            audio_np = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / MAX_INT16
            
            if len(audio_np) < RATE * 0.5:  # 0.5s minimum
                self.log.warning("Audio too short for transcription")
                return ""
            
            # Use optimized transcription settings based on model type
            transcribe_options = {
                'fp16': (self.device == "cuda"),
                'task': 'transcribe',
                'no_speech_threshold': 0.6
            }
            
            # Only add language parameter for non-English models
            if not self.model_size.endswith('.en'):
                transcribe_options['language'] = 'en'
                
            result = self.model.transcribe(audio_np, **transcribe_options)
            
            transcription = result['text'].strip()
            
            if transcription:
                self._write_transcription_to_log(transcription)
            
            return transcription
            
        except Exception as e:
            raise STTException(
                f"Failed to transcribe audio bytes: {e}",
                context={"audio_bytes_length": len(audio_bytes)}
            )

```

---

## File: `services/stt_service_server.py`

**Path:** `services/stt_service_server.py`

```
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
    uvicorn.run(app, host="0.0.0.0", port=8002)


```

---

## File: `services/tts_client.py`

**Path:** `services/tts_client.py`

```
#!/usr/bin/env python3
"""
HTTP client for the TTS microservice.
Provides the same interface as the original TTS service but communicates via HTTP.
"""

import requests
import time
from .logger import app_logger
from .exceptions import TTSException

class TTSClient:
    """HTTP client for TTS microservice that mimics the original TTS service interface."""
    
    def __init__(self, host="127.0.0.1", port=8001, timeout=30):
        self.log = app_logger.get_logger("tts_client")
        self.base_url = f"http://{host}:{port}"
        self.timeout = timeout
        self.log.debug(f"TTS client initialized for {self.base_url}")
    
    def speak(self, text):
        """Send text to TTS microservice for speech synthesis."""
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/speak",
                json={"text": text},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                duration = time.time() - start_time
                self.log.debug(f"TTS speak request completed in {duration:.2f}s")
                return response.json()
            else:
                error_msg = f"TTS speak request failed: {response.status_code} - {response.text}"
                self.log.error(error_msg)
                raise TTSException(error_msg)
                
        except requests.exceptions.RequestException as e:
            error_msg = f"TTS service communication error: {e}"
            self.log.error(error_msg)
            raise TTSException(error_msg) from e
    
    def stream_speak(self, text_stream):
        """Stream text to TTS service for speech synthesis."""
        try:
            for text_chunk in text_stream:
                self.speak(text_chunk)
        except Exception as e:
            error_msg = f"Streaming TTS communication error: {e}"
            self.log.error(error_msg)
            raise TTSException(error_msg) from e

    def warmup(self):
        """Send warmup request to TTS microservice."""
        try:
            response = requests.post(
                f"{self.base_url}/warmup",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                self.log.debug("TTS service warmed up successfully")
                return response.json()
            else:
                error_msg = f"TTS warmup request failed: {response.status_code} - {response.text}"
                self.log.error(error_msg)
                raise TTSException(error_msg)
                
        except requests.exceptions.RequestException as e:
            error_msg = f"TTS service communication error during warmup: {e}"
            self.log.error(error_msg)
            raise TTSException(error_msg) from e
    
    def health_check(self):
        """Check if the TTS microservice is responsive."""
        try:
            response = requests.get(f"{self.base_url}/docs", timeout=5)
            return response.status_code == 200
        except:
            return False

```

---

## File: `services/tts_service.py`

**Path:** `services/tts_service.py`

```
import os
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

# Suppress specific warnings
import warnings
warnings.filterwarnings("ignore", message="dropout option adds dropout after all but last recurrent layer")
warnings.filterwarnings("ignore", message=".*weight_norm.* is deprecated")
warnings.filterwarnings("ignore", message="FutureWarning")

import torch
from kokoro import KPipeline
import sounddevice as sd
import numpy as np
import threading
import queue
import time
import re
from .logger import app_logger
from .exceptions import TTSException

class TTSService:
    """TTS using Kokoro with pre-buffered chunk streaming and seamless playback."""

    def __init__(self, voice_model='af_heart'):
        self.log = app_logger.get_logger("tts_service")
        self.device = self._get_device()
        self.voice_model = voice_model
        self.sample_rate = 24000
        self.pipeline = self._build_pipeline()
        self._stream = None

    def _get_device(self):
        """Determine the compute device (CUDA or CPU) for TTS."""
        if torch.cuda.is_available():
            try:
                gpu_name = torch.cuda.get_device_name(0)
                gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)  # GB
                self.log.info(f"TTS (Kokoro) running on GPU: {gpu_name} ({gpu_memory:.1f}GB)")
                return "cuda"
            except Exception as e:
                self.log.warning(f"CUDA is available but failed to initialize: {e}")
                self.log.warning("TTS (Kokoro) falling back to CPU")
                return "cpu"
        else:
            self.log.warning("TTS (Kokoro) running on CPU - GPU acceleration not available")
            return "cpu"

    def _build_pipeline(self):
        # Load the model and move it to the correct device
        pipeline = KPipeline(lang_code='a', repo_id='hexgrad/Kokoro-82M')
        pipeline.model.to(self.device)
        return pipeline


    def speak(self, text=None, chunks=None):
        if chunks is None:
            self.log.debug(f"Speaking full text: '{text}'")
            chunks = self._segment_text(text)
        else:
            self.log.debug(f"Speaking from {len(chunks)} pre-segmented chunks.")

        self.log.debug(f"Text segmented into {len(chunks)} chunks")
        for i, chunk in enumerate(chunks):
            self.log.debug(f"Chunk {i}: '{chunk[:50]}...'" if len(chunk) > 50 else f"Chunk {i}: '{chunk}'")

        def generate_audio(chunk, out_queue):
            try:
                # Use torch.no_grad() to reduce memory allocation during inference
                with torch.no_grad():
                    generator = self.pipeline(chunk, voice=self.voice_model)
                    audio_frames = []
                    for _, _, audio in generator:
                        if isinstance(audio, torch.Tensor):
                            audio_np = audio.detach().cpu().numpy()
                            del audio
                        else:
                            audio_np = audio

                        if audio_np.dtype != np.float32:
                            audio_np = audio_np.astype(np.float32) / np.iinfo(audio_np.dtype).max

                        audio_frames.append(audio_np)
                    
                    # Clear generator explicitly and empty cache
                    del generator
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                    
                    full_audio = np.concatenate(audio_frames)
                    out_queue.put(full_audio)
            except Exception as e:
                self.log.error(f"TTS generator error: {e}")
                out_queue.put(None)

        try:
            self._stream = sd.OutputStream(samplerate=self.sample_rate, channels=1, dtype='float32', blocksize=256)
            self._stream.start()

            # Process all chunks
            for i, chunk in enumerate(chunks):
                chunk_queue = queue.Queue()
                thread = threading.Thread(target=generate_audio, args=(chunk, chunk_queue))
                thread.start()

                audio_data = chunk_queue.get()
                if audio_data is not None and len(audio_data) > 0:
                    self.log.debug(f"Playing chunk {i} with {len(audio_data)} samples")
                    self._stream.write(audio_data)
                else:
                    self.log.warning(f"Chunk {i} returned no audio data")

                thread.join()

        except Exception as e:
            if "cuFFT" in str(e) or "CUDA" in str(e):
                self.log.warning("cuFFT or CUDA crash detected, attempting TTS pipeline recovery...")
                try:
                    self.pipeline = self._build_pipeline()
                    self.log.info("TTS pipeline recovered successfully")
                except Exception as rebuild_error:
                    self.log.error(f"Failed to rebuild TTS pipeline: {rebuild_error}")
            self.log.error(f"TTS playback error: {e}")
        finally:
            if self._stream:
                self._stream.stop()
                self._stream.close()
                self._stream = None

    def _segment_text(self, text, max_chars=200):  # Reduced for better memory management
        # First try to split by sentences
        sentences = re.split(r'(?<=[.?!])\s+', text)
        chunks, buffer = [], ""

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # If single sentence is too long, split by commas or clauses
            if len(sentence) > max_chars:
                # Split long sentences by commas or semicolons
                sub_parts = re.split(r'(?<=[,;])\s+', sentence)
                for part in sub_parts:
                    part = part.strip()
                    if len(buffer) + len(part) + 1 > max_chars:
                        if buffer:
                            chunks.append(buffer.strip())
                        buffer = part
                    else:
                        if buffer:
                            buffer += " " + part
                        else:
                            buffer = part
            else:
                # Normal sentence processing
                if len(buffer) + len(sentence) + 1 > max_chars:
                    if buffer:
                        chunks.append(buffer.strip())
                    buffer = sentence
                else:
                    if buffer:
                        buffer += " " + sentence
                    else:
                        buffer = sentence

        if buffer:
            chunks.append(buffer.strip())

        # Log chunk details for debugging
        self.log.debug(f"Text segmented into {len(chunks)} chunks (max {max_chars} chars each)")
        for i, chunk in enumerate(chunks[:3]):  # Log first 3 chunks only
            self.log.debug(f"Chunk {i}: '{chunk[:100]}{'...' if len(chunk) > 100 else ''}'")

        return chunks

    def warmup(self):
        self.log.debug("Warming up TTS pipeline...")
        try:
            generator = self.pipeline(" ", voice=self.voice_model)
            for _ in generator:
                pass
            self.log.info("TTS pipeline warmed up successfully")
        except Exception as e:
            self.log.error(f"TTS warmup failed: {e}")
            raise TTSException(f"TTS warmup failed: {e}")

    def stream_speak(self, chunk_iterator):
        """Speak using streaming chunks."""
        self.log.info("Starting streaming TTS...")
        try:
            self._stream = sd.OutputStream(samplerate=self.sample_rate, channels=1, dtype='float32', blocksize=256)
            self._stream.start()

            for chunk in chunk_iterator:
                self.log.debug(f"Received text chunk: {chunk[:50]}...")
                audio_data = self._generate_chunk_audio(chunk)
                if audio_data is not None and len(audio_data) > 0:
                    self.log.debug(f"Playing chunk with {len(audio_data)} samples")
                    self._stream.write(audio_data)
                else:
                    self.log.warning("Chunk returned no audio data")

        except Exception as e:
            self.log.error(f"TTS streaming playback error: {e}")
        finally:
            if self._stream:
                self._stream.stop()
                self._stream.close()
                self._stream = None

    def _generate_chunk_audio(self, chunk):
        """Generate audio for a text chunk."""
        def generate_audio(chunk, out_queue):
            try:
                # Use torch.no_grad() to reduce memory allocation during inference
                with torch.no_grad():
                    generator = self.pipeline(chunk, voice=self.voice_model)
                    audio_frames = []
                    for _, _, audio in generator:
                        if isinstance(audio, torch.Tensor):
                            audio_np = audio.detach().cpu().numpy()
                            del audio
                        else:
                            audio_np = audio

                        if audio_np.dtype != np.float32:
                            audio_np = audio_np.astype(np.float32) / np.iinfo(audio_np.dtype).max

                        audio_frames.append(audio_np)
                    
                    # Clear generator explicitly and empty cache
                    del generator
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                    
                    full_audio = np.concatenate(audio_frames)
                    out_queue.put(full_audio)
            except Exception as e:
                self.log.error(f"TTS generator error: {e}")
                out_queue.put(None)

        chunk_queue = queue.Queue()
        thread = threading.Thread(target=generate_audio, args=(chunk, chunk_queue))
        thread.start()

        audio_data = chunk_queue.get()
        thread.join()

        return audio_data

    def stop(self):
        """Immediately stop audio playback"""
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
            self.log.info("TTS playback stopped")

```

---

## File: `services/tts_service_server.py`

**Path:** `services/tts_service_server.py`

```
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


```

---

## File: `services/tts_streaming_client.py`

**Path:** `services/tts_streaming_client.py`

```
#!/usr/bin/env python3
"""
Enhanced TTS client with streaming support for microservices architecture.
Works with both the LLM streaming client and TTS microservice.
"""

import requests
import time
from typing import Iterator, Optional, Generator
from .logger import app_logger
from .exceptions import TTSException


class TTSStreamingClient:
    """Enhanced TTS client with streaming support for real-time text-to-speech."""
    
    def __init__(self, host="127.0.0.1", port=8001, timeout=30):
        self.log = app_logger.get_logger("tts_streaming_client")
        self.base_url = f"http://{host}:{port}"
        self.timeout = timeout
        self.log.debug(f"TTS streaming client initialized for {self.base_url}")
    
    def speak(self, text: str):
        """Send text to TTS microservice for speech synthesis."""
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/speak",
                json={"text": text},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                duration = time.time() - start_time
                self.log.debug(f"TTS speak request completed in {duration:.2f}s")
                return response.json()
            else:
                error_msg = f"TTS speak request failed: {response.status_code} - {response.text}"
                self.log.error(error_msg)
                raise TTSException(error_msg)
                
        except requests.exceptions.RequestException as e:
            error_msg = f"TTS service communication error: {e}"
            self.log.error(error_msg)
            raise TTSException(error_msg) from e
    
    def stream_speak(self, text_stream: Iterator[str], chunk_size: int = 100):
        """
        Stream text chunks to TTS service for real-time speech synthesis.
        
        Args:
            text_stream: Iterator yielding text chunks
            chunk_size: Minimum character length before sending to TTS
        """
        try:
            buffer = ""
            chunk_count = 0
            
            self.log.info("Starting streaming TTS...")
            
            for text_chunk in text_stream:
                if not text_chunk:
                    continue
                    
                buffer += text_chunk
                
                # Send buffer to TTS when it reaches chunk_size or contains sentence endings
                if (len(buffer) >= chunk_size or 
                    any(punct in buffer for punct in ['.', '!', '?', '\n'])):
                    
                    # Find the best break point
                    break_point = self._find_break_point(buffer)
                    if break_point > 0:
                        chunk_to_speak = buffer[:break_point].strip()
                        buffer = buffer[break_point:].strip()
                        
                        if chunk_to_speak:
                            self.log.debug(f"Streaming chunk {chunk_count}: '{chunk_to_speak[:50]}...'")
                            self.speak(chunk_to_speak)
                            chunk_count += 1
            
            # Speak any remaining text in buffer
            if buffer.strip():
                self.log.debug(f"Final chunk {chunk_count}: '{buffer[:50]}...'")
                self.speak(buffer.strip())
                chunk_count += 1
            
            self.log.info(f"Streaming TTS completed with {chunk_count} chunks")
                
        except Exception as e:
            error_msg = f"Streaming TTS communication error: {e}"
            self.log.error(error_msg)
            raise TTSException(error_msg) from e
    
    def _find_break_point(self, text: str) -> int:
        """Find the best point to break text for TTS streaming."""
        # Look for sentence endings first
        for i in range(len(text) - 1, -1, -1):
            if text[i] in '.!?':
                return i + 1
        
        # Look for comma or other punctuation
        for i in range(len(text) - 1, -1, -1):
            if text[i] in ',:;':
                return i + 1
        
        # Look for word boundaries
        for i in range(len(text) - 1, -1, -1):
            if text[i] == ' ':
                return i + 1
        
        # If no good break point found, return full length
        return len(text)
    
    def stream_from_llm(self, llm_stream: Iterator[dict], text_key: str = "content"):
        """
        Stream TTS directly from LLM streaming output.
        
        Args:
            llm_stream: Iterator yielding LLM response dictionaries
            text_key: Key to extract text content from LLM response
        """
        def extract_text():
            for chunk in llm_stream:
                if isinstance(chunk, dict) and text_key in chunk:
                    yield chunk[text_key]
                elif isinstance(chunk, str):
                    yield chunk
        
        self.stream_speak(extract_text())
    
    def warmup(self):
        """Send warmup request to TTS microservice."""
        try:
            response = requests.post(
                f"{self.base_url}/warmup",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                self.log.debug("TTS service warmed up successfully")
                return response.json()
            else:
                error_msg = f"TTS warmup request failed: {response.status_code} - {response.text}"
                self.log.error(error_msg)
                raise TTSException(error_msg)
                
        except requests.exceptions.RequestException as e:
            error_msg = f"TTS service communication error during warmup: {e}"
            self.log.error(error_msg)
            raise TTSException(error_msg) from e
    
    def health_check(self):
        """Check if the TTS microservice is responsive."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False


class LLMToTTSStreamingBridge:
    """Bridge class to connect streaming LLM output directly to TTS input."""
    
    def __init__(self, tts_client: TTSStreamingClient):
        self.tts_client = tts_client
        self.log = app_logger.get_logger("llm_tts_bridge")
    
    def stream_llm_to_tts(self, llm_stream: Iterator[dict], 
                         chunk_size: int = 100,
                         text_key: str = "content"):
        """
        Stream LLM output directly to TTS with optimized chunking.
        
        Args:
            llm_stream: Iterator yielding LLM response dictionaries
            chunk_size: Minimum character length before sending to TTS
            text_key: Key to extract text content from LLM response
        """
        self.log.info("Starting LLM to TTS streaming bridge...")
        
        def text_generator():
            for chunk in llm_stream:
                if isinstance(chunk, dict):
                    if text_key in chunk and chunk[text_key]:
                        yield chunk[text_key]
                    # Log metrics if available
                    if "metrics" in chunk:
                        metrics = chunk["metrics"]
                        self.log.debug(f"LLM metrics: {metrics}")
                elif isinstance(chunk, str) and chunk:
                    yield chunk
        
        try:
            self.tts_client.stream_speak(text_generator(), chunk_size=chunk_size)
            self.log.info("LLM to TTS streaming completed successfully")
        except Exception as e:
            self.log.error(f"LLM to TTS streaming failed: {e}")
            raise


# Convenience function for easy integration
def create_streaming_tts_client(host="127.0.0.1", port=8001) -> TTSStreamingClient:
    """Create and return a configured streaming TTS client."""
    return TTSStreamingClient(host=host, port=port)


def create_llm_tts_bridge(tts_host="127.0.0.1", tts_port=8001) -> LLMToTTSStreamingBridge:
    """Create and return a configured LLM to TTS streaming bridge."""
    tts_client = create_streaming_tts_client(host=tts_host, port=tts_port)
    return LLMToTTSStreamingBridge(tts_client)

```

---

## File: `services/web_search_service.py`

**Path:** `services/web_search_service.py`

```
import os
import requests
from dotenv import load_dotenv

load_dotenv()

class WebSearchService:
    def __init__(self):
        self.api_key = os.getenv("TRAVILY_API")
        self.api_url = "https://api.tavily.com/search"
        if not self.api_key:
            raise ValueError("TRAVILY_API key not found in .env file.")

    def search(self, query, num_results=3):
        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": "basic",
            "max_results": num_results
        }

        try:
            print(f"[DEBUG] Query: {query}")
            print(f"[DEBUG] Payload: {payload}")

            response = requests.post(self.api_url, json=payload, timeout=5)
            response.raise_for_status()
            data = response.json()
            print(f"[DEBUG] Response: {response.status_code} {response.text}")


            results = []
            for r in data.get("results", []):
                results.append({
                    "title": r.get("title", ""),
                    "snippet": r.get("content", ""),
                    "url": r.get("url", "")
                })
            return results

        except Exception as e:
            print(f"🌐 Search error: {e}")
            return []


```

---


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


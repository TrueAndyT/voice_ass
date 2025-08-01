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



import ollama
import os
import time
from datetime import datetime
from .logger import app_logger
from .exceptions import LLMException, ResourceException, ConfigurationException
from .web_search_service import WebSearchService
from .file_search_service import FileSearchService
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
        self.dialog_log_file = None

        self.text = LLMText()
        self.intent_detector = IntentDetector()
        self.tts = TTSService()
        self.web = WebSearchService()
        self.search = FileSearchService()
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
                return reply if intent != "file_search" else ""

            # Default: general LLM chat
            self.history.append({'role': 'user', 'content': prompt})
            response = ollama.chat(model=self.model, messages=self.history[-16:])
            reply = response['message']['content']
            self.history.append({'role': 'assistant', 'content': reply})
            self._append_to_dialog_log("ASSISTANT", reply)
            return reply
            
        except ollama.ResponseError as e:
            error_message = f"Ollama API error: {e.error}"
            self.log.error(error_message, extra={
                "props": {"status_code": e.status_code}
            })
            self._append_to_dialog_log("ASSISTANT_ERROR", error_message)
            return "I'm sorry, I'm having trouble connecting to my brain right now."
        except Exception as e:
            error_message = f"Unexpected error in LLM service: {e}"
            self.log.critical(error_message, exc_info=True)
            self._append_to_dialog_log("ASSISTANT_ERROR", error_message)
            raise LLMException(error_message) from e

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

import ollama
import os
from datetime import datetime
from services.web_search_service import WebSearchService
from services.file_search_service import FileSearchService
from services.tts_service import TTSService
from services.intent_detector import IntentDetector
from services.llm_text import LLMText
from services.handlers.file_search_handler import FileSearchHandler
from services.handlers.memory_handler import MemoryHandler
from services.handlers.web_search_handler import WebSearchHandler
from services.handlers.note_handler import NoteHandler


class LLMService:
    def __init__(self, model='mistral'):
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
        }

    def _build_system_prompt(self):
        memory_block = ""
        try:
            if os.path.exists(self.memory_path):
                with open(self.memory_path, "r") as f:
                    memories = [line.strip() for line in f if line.strip()]
                    if memories:
                        memory_lines = [f"- {m}" for m in memories]
                        memory_block = "[MEMORY]\n" + "\n".join(memory_lines) + "\n[/MEMORY]\n\n"
        except:
            pass

        try:
            with open("config/system_prompt.txt", "r") as f:
                personality = f.read().strip()
        except:
            personality = "You are Sandy — a helpful voice assistant."

        return memory_block + personality

    def _create_new_dialog_log(self):
        os.makedirs("logs", exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.dialog_log_file = os.path.join("logs", f"dialog_{timestamp}.log")
        self._append_to_dialog_log("SYSTEM", self.system_prompt['content'])

    def _append_to_dialog_log(self, role, text):
        try:
            timestamp = datetime.now().strftime("%d-%m-%H-%M-%S")
            with open(self.dialog_log_file, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {role}: {text.strip()}\n")
        except:
            pass

    def warmup_llm(self):
        try:
            ollama.chat(model=self.model, messages=[
                {'role': 'system', 'content': 'You are a warmup agent.'},
                {'role': 'user', 'content': 'Just say: ready'}
            ])
            print("LLM warmed up.")
        except Exception as e:
            print(f"Warmup failed: {e}")

    def get_response(self, prompt):
        print("🧠 Thinking...")
        self._append_to_dialog_log("USER", prompt)

        intent = self.intent_detector.detect(prompt)
        self._append_to_dialog_log("INTENT", intent)

        if intent in self.handlers:
            reply = self.handlers[intent].handle(prompt)
            self._append_to_dialog_log("ASSISTANT", reply)
            return reply

        # Default: general LLM chat
        try:
            self.history.append({'role': 'user', 'content': prompt})
            response = ollama.chat(model=self.model, messages=self.history[-16:])
            reply = response['message']['content']
            self.history.append({'role': 'assistant', 'content': reply})
            self._append_to_dialog_log("ASSISTANT", reply)
            return reply
        except Exception as e:
            err = f"Error: {e}"
            self._append_to_dialog_log("ASSISTANT", err)
            return err

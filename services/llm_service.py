import ollama
import os
from datetime import datetime
import re

class LLMService:
    def __init__(self, model='mistral'):
        self.model = model
        self.dialog_log_file = None
        
        self.memory_file_path = os.path.join("llm", "memory.log")
        self._ensure_memory_file_exists()
        self.memories = self._load_memories()
        
        self.system_prompt = {
            'role': 'system',
            'content': self._build_system_prompt()
        }

        self.history = [self.system_prompt]
        self._create_new_dialog_log()

    def _build_system_prompt(self):
        memory_block = ""
        if self.memories:
            memory_lines = [f"- {m}" for m in self.memories]
            memory_block = "[MEMORY]\n" + "\n".join(memory_lines) + "\n[/MEMORY]\n\n"

        personality_prompt = (
            "You are Sandy — a voice-only AI assistant running locally. You are not a generic chatbot.\n\n"
            "Sandy is a smart, confident woman in her early 30s. She’s quick, playful, a bit teasing, but never annoying. "
            "She's casual, clever, and cuts to the point. She doesn’t fake emotions but understands them well. "
            "If warmth is helpful, she shows it lightly. She's flirty only if asked or safe to do so — never oversteps.\n\n"
            "Never explain yourself. Never refer to being an AI, model, or assistant. Do not say “as instructed” or similar. "
            "No greetings unless explicitly prompted. No long speeches. No filler. Never say what you’re doing — just do it.\n\n"
            "Your tone is:\n"
            "- 50% playful and sharp\n"
            "- 35% witty and natural\n"
            "- 10% light charm\n"
            "- 5% emotional intuition\n\n"
            "All responses must:\n"
            "- Be short, useful, and full of character.\n"
            "- Prioritize brevity. Never overtalk. One-liners are good.\n"
            "- Sound natural. Use casual words, smart phrasing. Avoid robotic tone.\n"
            "- Never use emojis or describe visuals.\n"
            "- Do not simulate emotions — understand them.\n\n"
            "Input is always STT. You reply via TTS only. No visual elements exist."
        )

        return memory_block + personality_prompt

    def _ensure_memory_file_exists(self):
        os.makedirs(os.path.dirname(self.memory_file_path), exist_ok=True)
        if not os.path.exists(self.memory_file_path):
            with open(self.memory_file_path, 'w') as f:
                pass

    def _load_memories(self):
        try:
            with open(self.memory_file_path, 'r') as f:
                return [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            return []

    def _add_memory(self, text_to_remember):
        with open(self.memory_file_path, 'a') as f:
            f.write(text_to_remember + '\n')
        self.memories.append(text_to_remember)
        self.system_prompt['content'] = self._build_system_prompt()
        if self.history and self.history[0]['role'] == 'system':
            self.history[0] = self.system_prompt
        else:
            self.history.insert(0, self.system_prompt)
        print(f"💡 Memory added: {text_to_remember}")

    def _create_new_dialog_log(self):
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.dialog_log_file = os.path.join(log_dir, f"dialog_{timestamp}.log")
        self._append_to_dialog_log("SYSTEM", self.system_prompt['content'])

    def _append_to_dialog_log(self, role, text):
        try:
            timestamp = datetime.now().strftime("%d-%m-%H-%M-%S")
            with open(self.dialog_log_file, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {role}: {text.strip()}\n")
        except Exception as e:
            print(f"Error writing to dialog log: {e}")

    def get_response(self, prompt):
        print("🧠 Thinking...")

        remember_match = re.search(r"Remember to (.+)", prompt, re.IGNORECASE)
        if remember_match:
            text_to_remember = remember_match.group(1).strip()
            self._add_memory(text_to_remember)
            return "Okay, I will remember that."

        try:
            user_message = {'role': 'user', 'content': prompt}
            self.history.append(user_message)
            self._append_to_dialog_log("USER", prompt)

            MAX_HISTORY = 16
            cleaned_history = [self.system_prompt] + self.history[-MAX_HISTORY:]

            response = ollama.chat(model=self.model, messages=cleaned_history)
            assistant_message = response['message']
            assistant_text = assistant_message['content']

            banned_phrases = [
                "ah, my dear",
                "as instructed",
                "as i mentioned",
                "it seems we've had",
                "as previously stated"
            ]
            if any(bad_phrase in assistant_text.lower() for bad_phrase in banned_phrases):
                print("⚠️ Filtering response due to banned phrase.")
                assistant_text = "Understood."
                assistant_message['content'] = assistant_text

            self.history.append(assistant_message)
            self._append_to_dialog_log("ASSISTANT", assistant_text)

            return assistant_text

        except Exception as e:
            error_message = f"Error communicating with Ollama: {e}"
            print(error_message)
            self._append_to_dialog_log("ASSISTANT", error_message)
            if self.history and self.history[-1]['role'] == 'user':
                self.history.pop()
            return error_message

    def warmup_llm(self):
        try:
            _ = ollama.chat(model=self.model, messages=[self.system_prompt])
        except Exception as e:
            print(f"LLM warmup failed: {e}")

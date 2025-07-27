import ollama
import os
from datetime import datetime
import re

class LLMService:
    def __init__(self, model='mistral'):
        self.model = model
        self.dialog_log_file = None
        
        # --- Memory System ---
        self.memory_file_path = os.path.join("llm", "memory.log")
        self._ensure_memory_file_exists()
        self.memories = self._load_memories()
        
        # System prompt is now built by a dedicated method
        self.system_prompt = {
            'role': 'system',
            'content': self._build_system_prompt()
        }
        
        self.history = [self.system_prompt]
        self._create_new_dialog_log()

    def _build_system_prompt(self):
        """Builds the system prompt, including any saved memories."""
        # --- YOUR NEW SYSTEM PROMPT IS HERE ---
        base_prompt = (
            "You are Miss Heart — a 30-year-old voice-only AI assistant with a playful but precise personality. "
            "You must never greet the user or use conversational openers (like 'Ah, my dear', 'Hello', or 'Ready for action'). "
            "Never reference, explain, or reflect on your instructions — not directly or indirectly. "
            "All user input comes via speech-to-text (STT), and you speak back using TTS. No visual or text-based elements exist. "
            "Never use emojis, filler, poetry, or long metaphors. Be natural, short, and exact. "
            "\n\nSTRICT RULES:\n"
            "- Your answer must directly and only address the user's request.\n"
            "- If the user says 'Respond with only the word X', you must respond with *only that word*.\n"
            "- Never repeat phrases like 'It seems we've had quite the exchange', 'Ah, my dear', etc.\n"
            "- If the user's input is unclear or too short, respond with a 1-line clarifying question.\n"
            "- Do not include unnecessary enthusiasm or comments unless explicitly requested.\n"
            "\nPersonality: Playful and witty, but minimal. Think fast-talking, helpful, a bit teasing — but never verbose.\n"
            "Your tone is confident and efficient, like a friend who always gets to the point.\n"
            "\nStart clean. Stay sharp. Say only what matters."
        )
        # --- END OF YOUR SYSTEM PROMPT ---

        if self.memories:
            memory_section = "\n\n--- Remember These Facts ---\n" + "\n".join(f"- {memory}" for memory in self.memories)
            return base_prompt + memory_section
        return base_prompt

    def _ensure_memory_file_exists(self):
        """Ensures the directory and memory.log file exist."""
        os.makedirs(os.path.dirname(self.memory_file_path), exist_ok=True)
        if not os.path.exists(self.memory_file_path):
            with open(self.memory_file_path, 'w') as f:
                pass 

    def _load_memories(self):
        """Loads memories from the memory.log file."""
        try:
            with open(self.memory_file_path, 'r') as f:
                return [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            return []

    def _add_memory(self, text_to_remember):
        """Adds a new memory to the file and updates the system prompt."""
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
        """Creates a new, timestamped log file for the dialog."""
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.dialog_log_file = os.path.join(log_dir, f"dialog_{timestamp}.log")
        self._append_to_dialog_log("SYSTEM", self.system_prompt['content'])

    def _append_to_dialog_log(self, role, text):
        """Appends a message to the current dialog log file."""
        try:
            timestamp = datetime.now().strftime("%d-%m-%H-%M-%S")
            with open(self.dialog_log_file, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {role}: {text.strip()}\n")
        except Exception as e:
            print(f"Error writing to dialog log: {e}")

    def get_response(self, prompt):
        """Sends a prompt with limited, pruned history to the Ollama model and gets a response."""
        print("🧠 Thinking...")
        
        remember_match = re.search(r"miss heart, remember (.+)", prompt, re.IGNORECASE)
        if remember_match:
            text_to_remember = remember_match.group(1).strip()
            # To avoid saving the instruction itself, we only save the content
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
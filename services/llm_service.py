import ollama
import os
from datetime import datetime
import re

class LLMService:
    def __init__(self, model='mistral'):
        self.model = model
        self.dialog_log_file = None

        self.memory_file_path = os.path.join("llm", "memory.log")
        self.system_prompt_path = os.path.join("llm", "system_prompt.txt")
        self._ensure_memory_file_exists()
        self.memories = self._load_memories()

        self.system_prompt = {
            'role': 'system',
            'content': self._build_system_prompt()
        }

        self.history = [self.system_prompt]
        self._create_new_dialog_log()

    def _build_system_prompt(self):
        try:
            with open(self.system_prompt_path, "r", encoding="utf-8") as f:
                base_prompt = f.read().strip()
        except FileNotFoundError:
            base_prompt = "You are Sandy, a voice-only assistant."

        memory_block = ""
        if self.memories:
            memory_lines = [f"- {m}" for m in self.memories]
            memory_block = "[MEMORY]\n" + "\n".join(memory_lines) + "\n[/MEMORY]\n\n"

        return memory_block + base_prompt

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
        self.memories = self._load_memories()
        self.system_prompt['content'] = self._build_system_prompt()
        if self.history and self.history[0]['role'] == 'system':
            self.history[0] = self.system_prompt
        else:
            self.history.insert(0, self.system_prompt)
        print(f"💡 Memory added: {text_to_remember}")

    def list_memories(self):
        self.memories = self._load_memories()
        if not self.memories:
            return "Nothing stored yet. I’m a clean slate."

        count = len(self.memories)
        plural = "thing" if count == 1 else "things"
        memory_lines = "\n".join([f"{i+1}. {m}" for i, m in enumerate(self.memories)])

        return (
            f"You’ve got {count} {plural} saved. Want to hear them?\n"
            f"Here’s what I’ve got stored:\n{memory_lines}"
        )

    def remove_memory(self, index: int):
        self.memories = self._load_memories()
        if 0 <= index < len(self.memories):
            self.memories.pop(index)
            with open(self.memory_file_path, 'w') as f:
                f.write("\n".join(self.memories) + "\n")
            self.system_prompt['content'] = self._build_system_prompt()
            self.history[0] = self.system_prompt
            return f"Gone. Memory {index+1} has been erased."
        return "Hmm. That memory number doesn’t exist."

    def update_memory(self, index: int, new_text: str):
        self.memories = self._load_memories()
        if 0 <= index < len(self.memories):
            self.memories[index] = new_text
            with open(self.memory_file_path, 'w') as f:
                f.write("\n".join(self.memories) + "\n")
            self.system_prompt['content'] = self._build_system_prompt()
            self.history[0] = self.system_prompt
            return f"Done. I’ve updated memory {index+1} with your new note."
        return "Can’t update. That memory number’s out of range."

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

        word_to_number = {
            'one': 1, 'two': 2, 'three': 3, 'four': 4,
            'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9
        }

        # --- Memory commands ---
        remember_match = re.search(r"remember to (.+)", prompt, re.IGNORECASE)
        if remember_match:
            text_to_remember = remember_match.group(1).strip()
            self._add_memory(text_to_remember)
            return "Got it. I’ll keep that in mind."

        if re.fullmatch(r"list memory|list memories", prompt.strip(), re.IGNORECASE):
            return self.list_memories()

        match_remove = re.match(r"remove memory (\w+)", prompt, re.IGNORECASE)
        if match_remove:
            token = match_remove.group(1).lower()
            idx = int(token) - 1 if token.isdigit() else word_to_number.get(token, -1) - 1
            if idx >= 0:
                return self.remove_memory(idx)

        match_update = re.match(r"update memory (\w+) to (.+)", prompt, re.IGNORECASE)
        if match_update:
            token = match_update.group(1).lower()
            new_text = match_update.group(2).strip()
            idx = int(token) - 1 if token.isdigit() else word_to_number.get(token, -1) - 1
            if idx >= 0:
                return self.update_memory(idx, new_text)

        # --- LLM with single-time memory injection ---
        user_message = {'role': 'user', 'content': prompt}
        self.history.append(user_message)
        self._append_to_dialog_log("USER", prompt)

        MAX_HISTORY = 16
        inject_prompt = self.system_prompt.copy()

        if self.history and self.history[0]['role'] == 'system':
            inject_prompt['content'] = re.sub(r"\[MEMORY\](.*?)\[/MEMORY\]", "", inject_prompt['content'], flags=re.DOTALL)

        cleaned_history = [inject_prompt] + self.history[-MAX_HISTORY:]

        try:
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

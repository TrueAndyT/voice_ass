import ollama
import os
import re
from datetime import datetime
from services.web_search_service import WebSearchService
from services.file_search_service import FileSearchService

class LLMService:
    def __init__(self, model='mistral'):
        self.model = model
        self.dialog_log_file = None

        self.memory_file_path = os.path.join("llm", "memory.log")
        self._ensure_memory_file_exists()
        self.memories = self._load_memories()

        self.web_search_service = WebSearchService()
        self.file_search_service = FileSearchService()

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

        try:
            with open(os.path.join("llm", "system_prompt.txt"), "r", encoding="utf-8") as f:
                personality_prompt = f.read().strip()
        except Exception as e:
            personality_prompt = "You are Sandy — a helpful voice assistant."

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
        self._regenerate_system_prompt()
        print(f"💡 Memory added: {text_to_remember}")

    def _update_memory(self, index, new_text):
        if 0 <= index < len(self.memories):
            old = self.memories[index]
            self.memories[index] = new_text
            with open(self.memory_file_path, 'w') as f:
                f.write('\n'.join(self.memories) + '\n')
            self._regenerate_system_prompt()
            print(f"🔁 Memory updated: '{old}' → '{new_text}'")

    def _remove_memory(self, index):
        if 0 <= index < len(self.memories):
            removed = self.memories.pop(index)
            with open(self.memory_file_path, 'w') as f:
                f.write('\n'.join(self.memories) + '\n')
            self._regenerate_system_prompt()
            print(f"🗑️ Memory removed: {removed}")

    def _regenerate_system_prompt(self):
        self.system_prompt['content'] = self._build_system_prompt()
        if self.history and self.history[0]['role'] == 'system':
            self.history[0] = self.system_prompt
        else:
            self.history.insert(0, self.system_prompt)

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

        # Memory operations
        remember_match = re.search(r"Remember to (.+)", prompt, re.IGNORECASE)
        if remember_match:
            text = remember_match.group(1).strip()
            self._add_memory(text)
            return "Okay, I’ll keep that in mind."

        update_match = re.search(r"update memory (\d+) to (.+)", prompt, re.IGNORECASE)
        if update_match:
            index = int(update_match.group(1)) - 1
            new_text = update_match.group(2).strip()
            self._update_memory(index, new_text)
            return f"Memory {index+1} updated."

        remove_match = re.search(r"remove memory (\d+)", prompt, re.IGNORECASE)
        if remove_match:
            index = int(remove_match.group(1)) - 1
            self._remove_memory(index)
            return f"Memory {index+1} removed."

        if re.search(r"list memories", prompt, re.IGNORECASE):
            if not self.memories:
                return "I don’t have anything saved yet."
            return "Here’s what I remember:\n" + '\n'.join([f"{i+1}. {m}" for i, m in enumerate(self.memories)])

        # Local file search
        file_search_match = re.search(r"(find|search|locate|where is) (.+)", prompt, re.IGNORECASE)
        if file_search_match:
            keyword = file_search_match.group(2).strip()
            file_results = self.file_search_service.search(keyword)

            filename_matches = file_results.get("filename_matches", [])
            content_matches = file_results.get("content_matches", [])

            if not filename_matches and not content_matches:
                reply = "I looked around but didn’t find anything matching that."
            else:
                reply = "Here’s what I found:\n"
                if filename_matches:
                    reply += "- Matching filenames:\n" + "\n".join(f"  - {f}" for f in filename_matches[:3]) + "\n"
                if content_matches:
                    reply += "- Files containing it:\n" + "\n".join(f"  - {f}" for f in content_matches[:3])

            self._append_to_dialog_log("ASSISTANT", reply)
            return reply

        # Web search
        if self._is_search_prompt(prompt):
            return self._handle_search_query(prompt)

        # Default: normal LLM chat
        try:
            user_message = {'role': 'user', 'content': prompt}
            self.history.append(user_message)

            MAX_HISTORY = 16
            cleaned_history = [self.system_prompt] + self.history[-MAX_HISTORY:]

            response = ollama.chat(model=self.model, messages=cleaned_history)
            assistant_message = response['message']
            assistant_text = assistant_message['content']

            self.history.append(assistant_message)
            self._append_to_dialog_log("ASSISTANT", assistant_text)

            return assistant_text

        except Exception as e:
            error = f"Error communicating with Ollama: {e}"
            print(error)
            self._append_to_dialog_log("ASSISTANT", error)
            if self.history and self.history[-1]['role'] == 'user':
                self.history.pop()
            return error

    def _is_search_prompt(self, prompt):
        prompt_lower = prompt.lower()
        return any(prompt_lower.startswith(p) for p in [
            "search", "look up", "what is", "who is", "find", "tell me about"
        ])

    def _handle_search_query(self, prompt):
        results = self.web_search_service.search(prompt)
        if not results:
            msg = "Couldn’t find anything juicy."
            self._append_to_dialog_log("ASSISTANT", msg)
            return msg

        sources = "\n\n".join(
            f"[{i+1}] {item['title']}\n{item['snippet']}\n(Source: {item['url']})"
            for i, item in enumerate(results)
        )

        summarization_prompt = {
            "role": "user",
            "content": (
                f"You are Sandy — summarize the following web search results into a short, clever spoken response. "
                f"Preserve your voice style: witty, brief, natural. Avoid long monologues. "
                f"Highlight only key points or facts. Use casual tone, and never mention this is from a search.\n\n"
                f"User asked: {prompt}\n\n"
                f"[WEB RESULTS]\n{sources}\n[/WEB RESULTS]"
            )
        }

        response = ollama.chat(
            model=self.model,
            messages=[self.system_prompt, summarization_prompt]
        )

        assistant_text = response['message']['content']
        self.history.append({"role": "user", "content": prompt})
        self.history.append({"role": "assistant", "content": assistant_text})
        self._append_to_dialog_log("ASSISTANT", assistant_text)
        return assistant_text

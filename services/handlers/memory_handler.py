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

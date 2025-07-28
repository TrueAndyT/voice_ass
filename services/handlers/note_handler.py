import re
import os
from datetime import datetime

class NoteHandler:
    def __init__(self, note_path="config/notes.json"):
        self.path = note_path
        self._ensure_file()
        self.notes = self._load()

    def _ensure_file(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        if not os.path.exists(self.path):
            with open(self.path, "w") as f:
                f.write("[]")

    def _load(self):
        import json
        with open(self.path, "r") as f:
            return json.load(f)

    def _save(self):
        import json
        with open(self.path, "w") as f:
            json.dump(self.notes, f, indent=2)

    def can_handle(self, prompt):
        return bool(re.search(r"\b(note|notes|take a note|delete note|show notes)\b", prompt, re.IGNORECASE))

    def handle(self, prompt):
        if m := re.search(r"take a note[:\-]?\s*(.+)", prompt, re.IGNORECASE):
            self.notes.append({"text": m.group(1).strip(), "timestamp": datetime.now().isoformat()})
            self._save()
            return "Got it. Note saved."

        if re.search(r"(show|list) notes", prompt, re.IGNORECASE):
            if not self.notes:
                return "You have no notes yet."
            return "Here are your notes:\n" + "\n".join(
                f"{i+1}. {n['text']}" for i, n in enumerate(self.notes))

        if m := re.search(r"delete note (\d+)", prompt, re.IGNORECASE):
            idx = int(m.group(1)) - 1
            if 0 <= idx < len(self.notes):
                removed = self.notes.pop(idx)
                self._save()
                return f"Deleted note: {removed['text']}"
            return "Couldn’t find that note to delete."

        return "I’m not sure what to do with that note request."

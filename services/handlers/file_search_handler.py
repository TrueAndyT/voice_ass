import subprocess
from pathlib import Path

class FileSearchHandler:
    def __init__(self, file_search_service, tts, text):
        self.search_service = file_search_service
        self.tts = tts
        self.text = text

    def handle(self, prompt: str) -> str:
        result = self.search_service.search(prompt)
        exact = result.get("exact_matches", [])
        fuzzy = result.get("fuzzy_matches", [])
        content = result.get("content_matches", [])
        all_found = result.get("all_results", [])

        if not all_found:
            reply = self.text.get("search.none")
            self.tts.speak("No matches found.")
            return reply

        count = len(all_found)
        spoken = self.text.format("search.found_prefix", count=count, plural="s" if count != 1 else "")
        reply = spoken + "\n"

        if content:
            reply += "- In file content:\n" + "\n".join(f"  - {f}" for f in content[:5]) + "\n"
        if exact:
            reply += "- Exact filenames:\n" + "\n".join(f"  - {f}" for f in exact[:5]) + "\n"
        if fuzzy:
            reply += "- Fuzzy matches:\n" + "\n".join(f"  - {f}" for f in fuzzy[:5]) + "\n"

        if count == 1:
            subprocess.run(["xdg-open", all_found[0]], check=False)

        if count <= 3:
            to_say = spoken + " " + ". ".join(Path(f).stem for f in all_found)
        else:
            to_say = spoken
        self.tts.speak(to_say)

        return reply

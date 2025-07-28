from pathlib import Path
from typing import List, Dict
import os
import re
from difflib import get_close_matches

class FileSearchService:
    def __init__(self):
        self.search_dirs = [
            Path.home() / "Downloads",
            Path.home() / "Documents",
            Path.home() / "Music",
            Path("/mnt/d"),
        ]

    def _get_extension_filter(self, prompt: str):
        match = re.search(r"\b(pdf|txt|docx|mp3|image|jpeg|png)\b", prompt.lower())
        if match:
            ext = match.group(1)
            if ext == "image":
                return (".jpg", ".jpeg", ".png")
            return (f".{ext}",)
        return ()

    def search(self, query: str) -> Dict[str, List[str]]:
        filename_matches = []
        fuzzy_matches = []
        content_matches = []
        all_files = []

        ext_filter = self._get_extension_filter(query)

        for directory in self.search_dirs:
            if not directory.exists():
                continue
            for root, _, files in os.walk(directory):
                for file in files:
                    filepath = Path(root) / file
                    if ext_filter and not filepath.name.lower().endswith(ext_filter):
                        continue
                    all_files.append(str(filepath))

                    if query.lower() == filepath.stem.lower():
                        filename_matches.append(str(filepath))
                    elif file.endswith(('.txt', '.pdf', '.docx')):
                        try:
                            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                                if query.lower() in f.read().lower():
                                    content_matches.append(str(filepath))
                        except Exception:
                            continue

        file_stems = [Path(f).stem.lower() for f in all_files]
        close_matches = get_close_matches(query.lower(), file_stems, cutoff=0.7)
        fuzzy_matches = [
            f for f in all_files
            if Path(f).stem.lower() in close_matches and f not in filename_matches
        ]

        return {
            "filename_matches": filename_matches + fuzzy_matches,
            "content_matches": content_matches
        }

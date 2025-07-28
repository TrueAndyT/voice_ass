import os
import re
from pathlib import Path
from difflib import get_close_matches
from services.indexing_service import IndexingService

class FileSearchService:
    def __init__(self):
        self.indexer = IndexingService()

    def search(self, query: str):
        keyword, ext_filter = self._extract_query_details(query)
        indexed_data = self.indexer.load_index()  # list of (path, content)

        if not indexed_data:
            print("[INFO] Index is empty. Running indexing...")
            self.indexer.index_files()
            indexed_data = self.indexer.load_index()

        all_files = [path for path, _ in indexed_data]

        # Apply extension filter
        if ext_filter:
            indexed_data = [(path, content) for path, content in indexed_data if path.lower().endswith(f".{ext_filter.lower()}")]

        # Exact match
        exact_matches = [path for path, _ in indexed_data if keyword.lower() == Path(path).stem.lower()]

        # Fuzzy match
        file_stems = [Path(path).stem.lower() for path, _ in indexed_data]
        fuzzy_match_stems = get_close_matches(keyword.lower(), file_stems, n=5, cutoff=0.7)
        fuzzy_matches = [path for path, _ in indexed_data if Path(path).stem.lower() in fuzzy_match_stems]

        # Content match
        content_matches = [path for path, content in indexed_data if keyword.lower() in (content or "").lower()]

        # Merge deduplicated
        all_results = list(set(exact_matches + fuzzy_matches + content_matches))

        return {
            "exact_matches": exact_matches,
            "fuzzy_matches": fuzzy_matches,
            "content_matches": content_matches,
            "all_results": all_results
        }

    def _extract_query_details(self, prompt: str):
        ext_match = re.search(r"\b(pdf|txt|docx|md|mp3|wav|png|jpg|jpeg)\b", prompt.lower())
        ext_filter = ext_match.group(1) if ext_match else None

        keyword_match = re.search(r"(find|search|locate|where is)?\s*(.+)", prompt.lower())
        keyword = keyword_match.group(2).strip() if keyword_match else prompt.strip()

        return keyword, ext_filter

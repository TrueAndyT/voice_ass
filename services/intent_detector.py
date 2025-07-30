import re

class IntentDetector:
    def detect(self, prompt: str) -> str:
        if re.search(r"\b(remember to|update memory|remove memory|list memories)\b", prompt, re.IGNORECASE):
            return "memory"
        if re.search(r"\b(find|search|locate|where is)\b", prompt, re.IGNORECASE):
            return "file_search"
        if re.search(r"\b(search|look up|what is|who is|tell me about)\b", prompt.lower()):
            return "web_search"
        return "default"


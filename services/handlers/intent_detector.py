#!/usr/bin/env python3
"""
Simple intent detector used by LLMService.
Detects high-level intents used to route requests to specialized handlers.
"""
import re
from typing import Literal

Intent = Literal["file_search", "memory", "web_search", "note", "general"]

class IntentDetector:
    def detect(self, text: str) -> Intent:
        t = text.lower().strip()
        # File search intent
        if re.search(r"\b(find|search|locate|where is|look up)\b", t):
            return "file_search"
        # Memory intent (read/write memory file)
        if re.search(r"\b(memory|remember|forget|what do you remember)\b", t):
            return "memory"
        # Web search intent
        if re.search(r"\b(search the web|web search|google|duckduckgo|bing|online)\b", t):
            return "web_search"
        # Notes intent
        if re.search(r"\b(note|notes|take a note|delete note|show notes)\b", t):
            return "note"
        return "general"


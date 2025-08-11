#!/usr/bin/env python3
"""
Minimal text resources helper for templated strings used by handlers.
"""
from typing import Dict

_DEFAULTS: Dict[str, str] = {
    # Search
    "search.found_prefix": "I found {count} item{plural}:",
    "search.none": "I couldn’t find anything matching that.",

    # Web search
    "web.none": "I couldn’t find anything useful on the web.",
    "web.summary_prefix": "Summarize the following web results and answer the user's question clearly, citing sources when appropriate.",
}

class LLMText:
    def get(self, key: str) -> str:
        return _DEFAULTS.get(key, key)

    def format(self, key: str, **kwargs) -> str:
        template = self.get(key)
        try:
            return template.format(**kwargs)
        except Exception:
            return template


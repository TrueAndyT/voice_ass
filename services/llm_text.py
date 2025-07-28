import json
import os

class LLMText:
    def __init__(self, config_path="config/llm_responses.json"):
        self.data = {}
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                self.data = json.load(f)

    def get(self, key, default=""):
        return self.data.get(key, default)

    def format(self, key, **kwargs):
        template = self.get(key)
        return template.format(**kwargs) if template else ""

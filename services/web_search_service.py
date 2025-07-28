import os
import requests
from dotenv import load_dotenv

load_dotenv()

class WebSearchService:
    def __init__(self):
        self.api_key = os.getenv("TRAVILY_API")
        self.api_url = "https://api.tavily.com/search"
        if not self.api_key:
            raise ValueError("TRAVILY_API key not found in .env file.")

    def search(self, query, num_results=3):
        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": "basic",
            "max_results": num_results
        }

        try:
            response = requests.post(self.api_url, json=payload, timeout=5)
            response.raise_for_status()
            data = response.json()

            results = []
            for r in data.get("results", []):
                results.append({
                    "title": r.get("title", ""),
                    "snippet": r.get("content", ""),
                    "url": r.get("url", "")
                })
            return results

        except Exception as e:
            print(f"🌐 Search error: {e}")
            return []


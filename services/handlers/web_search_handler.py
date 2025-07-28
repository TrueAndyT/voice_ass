class WebSearchHandler:
    def __init__(self, web_search_service, model, system_prompt, text):
        self.web = web_search_service
        self.model = model
        self.system_prompt = system_prompt
        self.text = text

    def handle(self, prompt: str) -> str:
        import ollama

        results = self.web.search(prompt)
        if not results:
            return self.text.get("web.none")

        sources = "\n\n".join(
            f"[{i+1}] {item['title']}\n{item['snippet']}\n(Source: {item['url']})"
            for i, item in enumerate(results)
        )

        summarization_prompt = {
            "role": "user",
            "content": (
                f"{self.text.get('web.summary_prefix')}\n\n"
                f"User asked: {prompt}\n\n"
                f"[WEB RESULTS]\n{sources}\n[/WEB RESULTS]"
            )
        }

        response = ollama.chat(model=self.model, messages=[
            self.system_prompt, summarization_prompt
        ])
        return response['message']['content']

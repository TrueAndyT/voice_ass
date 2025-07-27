import ollama
import os
from datetime import datetime
import subprocess
import atexit
import time

class LLMService:
    def __init__(self, model='mistral'):
        self.model = model
        self.ollama_process = None
        self.dialog_log_file = None
        self.system_prompt = [{
            'role': 'system',
            'content': (
                "You are Miss Heart, a warm, caring, cheerful, and funny assistant. "
                "You never return source code or technical implementation details. "
                "All your replies are very short and precise, in a friendly tone."
                "Do not use emojies or special characters or markdown format in your responses - assume your reply will be voiced by a text-to-speech system."
            )
        }]
        self._start_ollama_server()
        self._create_new_dialog_log()

    def _start_ollama_server(self):
        try:
            ollama.list()
            print("Ollama server is already running.")
        except Exception:
            print("Ollama server not found. Starting it in the background...")
            try:
                self.ollama_process = subprocess.Popen(["ollama", "serve"],
                                                       stdout=subprocess.DEVNULL,
                                                       stderr=subprocess.DEVNULL)
                atexit.register(self._stop_ollama_server)
                for i in range(15):
                    print(f"Waiting for Ollama server to start... ({i+1}/15)", end='\r')
                    time.sleep(1)
                    try:
                        ollama.list()
                        print("\nOllama server started successfully.          ")
                        return
                    except Exception:
                        continue
                self._stop_ollama_server()
                raise RuntimeError("Failed to start Ollama server.")
            except Exception as e:
                print(f"\nError starting Ollama: {e}")
                raise

    def _stop_ollama_server(self):
        if self.ollama_process:
            print("\nShutting down the Ollama server...")
            self.ollama_process.terminate()
            self.ollama_process.wait()
            print("Ollama server has been shut down.")

    def _create_new_dialog_log(self):
        log_dir = "llm"
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%d-%m-%H-%M-%S")
        self.dialog_log_file = os.path.join(log_dir, f"dialog_{timestamp}.log")

    def reset_dialog_log(self):
        self._create_new_dialog_log()

    def _append_to_dialog_log(self, role, text):
        try:
            timestamp = datetime.now().strftime("%d-%m-%H-%M-%S")
            with open(self.dialog_log_file, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {role}: {text.strip()}\n")
        except Exception as e:
            print(f"Error writing to dialog log: {e}")

    def get_response(self, prompt):
        print("🧠 Thinking...")
        try:
            self._append_to_dialog_log("USER", prompt)
            messages = self.system_prompt + [{'role': 'user', 'content': prompt}]
            response = ollama.chat(model=self.model, messages=messages)
            content = response['message']['content']
            self._append_to_dialog_log("ASSISTANT", content)
            return content
        except Exception as e:
            error_message = f"Error communicating with Ollama: {e}"
            print(error_message)
            self._append_to_dialog_log("ASSISTANT", error_message)
            return error_message

    def summarize_intent(self, transcription):
        prompt = f"Summarize the user request in two words. Return only two words.\nRequest: {transcription}\nSummary:"
        messages = [{"role": "system", "content": "You summarize user requests in only two words. No explanations."},
                    {"role": "user", "content": prompt}]
        response = ollama.chat(model=self.model, messages=messages)
        return response['message']['content'].strip()

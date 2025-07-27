import subprocess
import threading
import time
import os

class MemoryLogger:
    def __init__(self, log_file='memory.log', interval=1):
        self.log_file = log_file
        self.interval = interval
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._log_vram_usage, daemon=True)

        # Clear the old log file at the start of a new session
        if os.path.exists(self.log_file):
            os.remove(self.log_file)

    def _get_vram_usage(self):
        """Executes nvidia-smi to get VRAM usage for specific processes."""
        try:
            # Get total used/total memory
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=memory.used,memory.total', '--format=csv,noheader,nounits'],
                capture_output=True, text=True, check=True
            )
            total_used, total_memory = result.stdout.strip().split(', ')

            # Get VRAM used by python processes (Whisper, TTS, etc.)
            result_python = subprocess.run(
                "nvidia-smi pmon -c 1 | awk '/python/ {sum+=$5} END {print sum}'",
                shell=True, capture_output=True, text=True
            )
            python_used = result_python.stdout.strip() or '0'

            # Get VRAM used by ollama
            result_ollama = subprocess.run(
                "nvidia-smi pmon -c 1 | awk '/ollama/ {sum+=$5} END {print sum}'",
                shell=True, capture_output=True, text=True
            )
            ollama_used = result_ollama.stdout.strip() or '0'

            return {
                "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
                "total_used": total_used,
                "total_memory": total_memory,
                "python_used": python_used,
                "ollama_used": ollama_used
            }
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None

    def _log_vram_usage(self):
        """Periodically logs VRAM usage to the specified file."""
        with open(self.log_file, 'w') as f:
            f.write("Timestamp, Total Used (MiB), Python Used (MiB), Ollama Used (MiB), Total Memory (MiB)\n")
            
            while not self._stop_event.is_set():
                usage = self._get_vram_usage()
                if usage:
                    f.write(
                        f"{usage['timestamp']}, "
                        f"{usage['total_used']}, "
                        f"{usage['python_used']}, "
                        f"{usage['ollama_used']}, "
                        f"{usage['total_memory']}\n"
                    )
                    f.flush()
                time.sleep(self.interval)

    def start(self):
        """Starts the background logging thread."""
        print("--- VRAM logger started ---")
        self._thread.start()

    def stop(self):
        """Stops the background logging thread."""
        self._stop_event.set()
        self._thread.join()
        print("--- VRAM logger stopped ---")
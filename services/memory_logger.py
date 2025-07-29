import subprocess
import threading
import time
import os
import psutil
from datetime import datetime

class MemoryLogger:
    TARGET_PROCESSES = ["python", "ollama", "openwakeword"]

    def __init__(self, log_file=os.path.join('logs', 'memory.csv'), interval=1):
        self.log_file = log_file
        self.interval = interval
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._log_metrics, daemon=True)

        log_dir = os.path.dirname(self.log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        if os.path.exists(self.log_file):
            os.remove(self.log_file)

    def _get_gpu_vram_by_name(self, name):
        """Returns total GPU memory used by processes with a given name using nvidia-smi pmon."""
        try:
            result = subprocess.run(
                "nvidia-smi pmon -c 1",
                shell=True, capture_output=True, text=True
            )
            lines = result.stdout.strip().splitlines()
            matching = [int(line.split()[4]) for line in lines if name in line]
            return sum(matching)
        except Exception:
            return 0

    def _get_total_gpu(self):
        """Returns (total used, total memory) from nvidia-smi."""
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=memory.used,memory.total', '--format=csv,noheader,nounits'],
                capture_output=True, text=True, check=True
            )
            used, total = result.stdout.strip().split(', ')
            return int(used), int(total)
        except Exception:
            return 0, 0

    def _get_process_stats(self):
        """Returns RAM and CPU usage for target processes."""
        stats = {name: {"ram": 0, "cpu": 0} for name in self.TARGET_PROCESSES}
        for proc in psutil.process_iter(['name', 'memory_info', 'cpu_percent']):
            try:
                name = proc.info['name']
                if name:
                    for target in self.TARGET_PROCESSES:
                        if target in name.lower():
                            stats[target]["ram"] += proc.memory_info().rss // (1024 * 1024)
                            stats[target]["cpu"] += proc.cpu_percent(interval=None)
            except Exception:
                continue
        return stats

    def _log_metrics(self):
        with open(self.log_file, 'w') as f:
            f.write("Time, GPU_Used, GPU_Total, GPU_Python, GPU_Ollama, GPU_OWW, "
                    "RAM_Python, RAM_Ollama, RAM_OWW, CPU_Python, CPU_Ollama, CPU_OWW\n")

            while not self._stop_event.is_set():
                now = datetime.now().strftime('%m-%d %H:%M:%S')
                gpu_used, gpu_total = self._get_total_gpu()
                gpu_python = self._get_gpu_vram_by_name("python")
                gpu_ollama = self._get_gpu_vram_by_name("ollama")
                gpu_oww = self._get_gpu_vram_by_name("openwakeword")

                proc_stats = self._get_process_stats()

                f.write(f"{now}, {gpu_used}, {gpu_total}, {gpu_python}, {gpu_ollama}, {gpu_oww}, "
                        f"{proc_stats['python']['ram']}, {proc_stats['ollama']['ram']}, {proc_stats['openwakeword']['ram']}, "
                        f"{proc_stats['python']['cpu']:.1f}, {proc_stats['ollama']['cpu']:.1f}, {proc_stats['openwakeword']['cpu']:.1f}\n")
                f.flush()

                time.sleep(self.interval)

    def start(self):
        print("--- VRAM logger started ---")
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        self._thread.join()
        print("--- VRAM logger stopped ---")

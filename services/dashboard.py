from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.text import Text
import psutil
import time
import threading

def get_service_pids(service_names=["stt", "tts", "llm"]):
    """Get the PIDs of all running microservices."""
    pids = {}
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Example command: ['python3', '-m', 'uvicorn', 'services.stt_service_server:app', ...]
            cmdline = proc.info.get('cmdline')
            if cmdline and "uvicorn" in cmdline and "services." in " ".join(cmdline):
                for service in service_names:
                    if f"services.{service}_service_server:app" in " ".join(cmdline):
                        pids[service] = proc.info['pid']
                        break
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return pids

class DashboardService:
    def __init__(self):
        self.console = Console()
        self.layout = self.make_layout()
        self.live = Live(self.layout, console=self.console, screen=True, redirect_stderr=False, vertical_overflow="visible")

        # Data attributes with thread lock
        self._lock = threading.Lock()
        self.assistant_state = "Initializing"
        self.intent = "N/A"
        self.audio_level = "0.00 / 0.00"
        self.stt_output = ""
        self.llm_output = ""
        self.perf_metrics = {}

        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self.update_loop, daemon=True)

    def make_layout(self):
        layout = Layout(name="root")
        layout.split(
            Layout(name="header", size=12),
            Layout(ratio=1, name="body"),
        )
        layout["body"].split_row(Layout(name="stt"), Layout(name="llm"))
        layout["header"].split(
            Layout(name="main_header"),
            Layout(name="performance", size=3)
        )
        return layout

    def update_layout(self):
        self.layout["main_header"].update(self.get_system_resources_panel())
        self.layout["performance"].update(self.get_performance_panel())
        self.layout["stt"].update(Panel(Text(self.stt_output), title="STT Output"))
        self.layout["llm"].update(Panel(Text(self.llm_output), title="LLM Output"))

    def get_system_resources_panel(self):
        # Create a table for system resources
        resources_table = Table.grid(expand=True)
        resources_table.add_column(justify="left", ratio=0.4)
        resources_table.add_column(justify="center", ratio=0.15)
        resources_table.add_column(justify="center", ratio=0.15)
        resources_table.add_column(justify="center", ratio=0.15)
        resources_table.add_column(justify="center", ratio=0.15)

        resources_table.add_row("Service", "CPU %", "RAM (MB)", "GPU %", "VRAM (MB)")
        resources_table.add_row("-" * 15, "-" * 5, "-" * 8, "-" * 5, "-" * 8)

        # App (Main) data
        try:
            app_process = psutil.Process()
            # Use interval-based CPU monitoring for accuracy
            app_cpu = app_process.cpu_percent(interval=0.1) / psutil.cpu_count()
            app_ram = app_process.memory_info().rss / (1024 * 1024)
            resources_table.add_row("App (Main)", f"{app_cpu:.1f}", f"{app_ram:.0f}", "-", "-")
        except psutil.NoSuchProcess:
            resources_table.add_row("App (Main)", "offline", "offline", "-", "-")

        # --- Microservices Data ---
        service_pids = get_service_pids(["stt", "tts"])
        service_names = {"stt": "Whisper", "tts": "Kokoro"}
        
        # --- GPU Data ---
        gpu_util, vram_used = 0, 0
        try:
            import subprocess
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=utilization.gpu,memory.used', '--format=csv,noheader,nounits'],
                capture_output=True, text=True, timeout=2
            )
            if result.returncode == 0 and result.stdout.strip():
                gpu_info = result.stdout.strip().split(', ')
                gpu_util = int(gpu_info[0])
                vram_used = int(gpu_info[1])
        except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
            pass # nvidia-smi not found or failed

        # --- Display Microservices (STT, TTS) ---
        for service_key, display_name in service_names.items():
            if service_key in service_pids:
                try:
                    process = psutil.Process(service_pids[service_key])
                    # Use interval-based CPU monitoring for accuracy
                    cpu = process.cpu_percent(interval=0.1) / psutil.cpu_count()
                    ram = process.memory_info().rss / (1024 * 1024)
                    
                    # Estimate GPU usage based on realistic VRAM distribution
                    if service_key == "stt" and gpu_util > 0:
                        # Whisper Tiny: ~300MB VRAM, light GPU usage
                        gpu_display = f"{min(gpu_util // 4, 15)}"
                        vram_display = "300" if vram_used > 300 else f"{int(vram_used * 0.04)}"
                    elif service_key == "tts" and gpu_util > 0:
                        # Kokoro 82M: ~800MB VRAM, light GPU usage
                        gpu_display = f"{min(gpu_util // 4, 15)}"
                        vram_display = "800" if vram_used > 800 else f"{int(vram_used * 0.11)}"
                    else:
                        gpu_display = "-"
                        vram_display = "-"
                        
                    resources_table.add_row(display_name, f"{cpu:.1f}", f"{ram:.0f}", gpu_display, vram_display)
                except psutil.NoSuchProcess:
                    resources_table.add_row(display_name, "offline", "offline", "-", "-")
            else:
                resources_table.add_row(display_name, "offline", "offline", "-", "-")

        # --- Find and Display Ollama ---
        ollama_pid = None
        for proc in psutil.process_iter(['pid', 'name']):
            if 'ollama' in proc.info.get('name', '').lower():
                ollama_pid = proc.info['pid']
                break
        
        if ollama_pid:
            try:
                process = psutil.Process(ollama_pid)
                # Use interval-based CPU monitoring for accuracy
                cpu = process.cpu_percent(interval=0.1) / psutil.cpu_count()
                ram = process.memory_info().rss / (1024 * 1024)
                # Ollama 8B Q4: ~5200MB VRAM, majority of GPU usage
                gpu_display = f"{max(gpu_util - 25, 0)}" if gpu_util > 0 else "-"
                # Ollama gets ~72% of total VRAM (5200/7200)
                ollama_vram = int(vram_used * 0.72) if vram_used > 0 else 0
                vram_display = f"{ollama_vram}"
                resources_table.add_row("Ollama", f"{cpu:.1f}", f"{ram:.0f}", gpu_display, vram_display)
            except psutil.NoSuchProcess:
                resources_table.add_row("Ollama", "offline", "offline", "-", "-")
        else:
            resources_table.add_row("Ollama", "offline", "offline", "-", "-")

        # Other info panels
        state_panel = Panel(Text(self.assistant_state, justify="center"), title="State")
        audio_panel = Panel(Text(self.audio_level, justify="center"), title="Audio")
        intent_panel = Panel(Text(self.intent, justify="center"), title="Intent")

        # Main system panel
        system_panel = Panel(
            resources_table,
            title="System Resources"
        )

        # Create a grid for the top panels
        top_grid = Table.grid(expand=True)
        top_grid.add_column(ratio=0.7)
        top_grid.add_column(ratio=0.15)
        top_grid.add_column(ratio=0.15)

        with self._lock:
            state_panel = Panel(Text(self.assistant_state, justify="center"), title="State")
            audio_panel = Panel(Text(self.audio_level, justify="center"), title="RMS Audio")
            intent_panel = Panel(Text(self.intent, justify="center"), title="Intent")

        top_grid.add_row(system_panel, state_panel, audio_panel, intent_panel)
        return Panel(top_grid, title="Voice Assistant Dashboard", border_style="blue")

    def get_performance_panel(self):
        perf_text = " | ".join([f"{k}: {v}" for k, v in self.perf_metrics.items()])
        return Panel(Text(perf_text, justify="center"), title="Performance Metrics")

    def update_loop(self):
        while not self.stop_event.is_set():
            self.update_layout()
            time.sleep(0.5)

    def start(self):
        self.live.start()
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        self.thread.join()
        self.live.stop()

    def update_state(self, new_state):
        with self._lock:
            self.assistant_state = new_state

    def update_intent(self, new_intent):
        with self._lock:
            self.intent = new_intent

    def update_audio_level(self, current_rms, threshold):
        with self._lock:
            self.audio_level = f"{current_rms:.2f} / {threshold:.2f}"

    def update_stt(self, text):
        with self._lock:
            self.stt_output = text

    def update_llm(self, text):
        with self._lock:
            self.llm_output = text

    def update_performance(self, metrics):
        with self._lock:
            self.perf_metrics.update(metrics)

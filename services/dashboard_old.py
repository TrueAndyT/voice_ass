from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.text import Text
import psutil
import time
import threading
import subprocess

class DashboardService:
    def __init__(self):
        self.console = Console()
        self.layout = self.make_layout()
        self.live = Live(self.layout, console=self.console, screen=True, redirect_stderr=False, vertical_overflow="visible")

        # --- Thread-safe data attributes ---
        self._lock = threading.Lock()
        self.assistant_state = "Initializing"
        self.intent = "N/A"
        self.audio_level = "0.00 / 0.00"
        self.stt_output = ""
        self.llm_output = ""
        self.perf_metrics = {}
        # New shared data structure for system resources
        self.system_resources = {} 

        # --- Threads ---
        self.stop_event = threading.Event()
        # UI thread for fast rendering
        self.ui_thread = threading.Thread(target=self._ui_update_loop, daemon=True)
        # Data collector thread for slow I/O
        self.data_thread = threading.Thread(target=self._data_collector_loop, daemon=True)

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

    def _ui_update_loop(self):
        """UI Thread: Renders the dashboard frequently with pre-collected data."""
        while not self.stop_event.is_set():
            # This is now very fast, just building the layout
            self.layout["main_header"].update(self.get_system_resources_panel())
            self.layout["performance"].update(self.get_performance_panel())
            self.layout["stt"].update(Panel(Text(self.stt_output), title="STT Output"))
            self.layout["llm"].update(Panel(Text(self.llm_output), title="LLM Output"))
            time.sleep(0.5) # UI refresh rate

    def _data_collector_loop(self):
        """Data Collector Thread: Performs slow I/O operations infrequently."""
        while not self.stop_event.is_set():
            resources = {}
            # --- Collect all slow data here ---
            
            # App (Main) Process
            try:
                app_process = psutil.Process()
                resources['App (Main)'] = {
                    'cpu': app_process.cpu_percent() / psutil.cpu_count(),
                    'ram': app_process.memory_info().rss / (1024 * 1024),
                    'gpu': '-',
                    'vram': '-'
                }
            except psutil.NoSuchProcess:
                pass
            
            # Microservices (STT, TTS)
            service_pids = self._get_service_pids(["stt", "tts"])
            for service_key, pid in service_pids.items():
                try:
                    proc = psutil.Process(pid)
                    resources[service_key] = {
                        'cpu': proc.cpu_percent() / psutil.cpu_count(),
                        'ram': proc.memory_info().rss / (1024 * 1024),
                    }
                except psutil.NoSuchProcess:
                    continue
            
            # Ollama
            ollama_pid = self._get_service_pids(["ollama"]).get("ollama")
            if ollama_pid:
                try:
                    proc = psutil.Process(ollama_pid)
                    resources['Ollama'] = {
                        'cpu': proc.cpu_percent() / psutil.cpu_count(),
                        'ram': proc.memory_info().rss / (1024 * 1024),
                    }
                except psutil.NoSuchProcess:
                    pass
            
            # GPU stats from nvidia-smi
            try:
                result = subprocess.run(
                    ['nvidia-smi', '--query-compute-apps=process_name,used_gpu_memory', '--format=csv,noheader,nounits'],
                    capture_output=True, text=True, check=True, timeout=2
                )
                for line in result.stdout.strip().splitlines():
                    name, mem = line.split(', ')
                    name = name.lower()
                    if 'python' in name: # Crude mapping for STT/TTS
                        if 'stt' in resources: resources['stt']['vram'] = mem
                        elif 'tts' in resources: resources['tts']['vram'] = mem
                    elif 'ollama' in name:
                        if 'Ollama' in resources: resources['Ollama']['vram'] = mem
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                pass
            
            # --- Safely update the shared data structure ---
            with self._lock:
                self.system_resources = resources
            
            time.sleep(2) # Collect data every 2 seconds

    def _get_service_pids(self, service_names=["stt", "tts", "llm", "ollama"]):
        """Helper to find PIDs of running services."""
        pids = {}
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline_str = " ".join(proc.info.get('cmdline', []))
                proc_name = proc.info.get('name', '').lower()

                if "ollama" in service_names and 'ollama' in proc_name:
                    pids['ollama'] = proc.info['pid']
                    continue
                
                if "uvicorn" in cmdline_str and "services." in cmdline_str:
                    for service in service_names:
                        if f"services.{service}_service_server:app" in cmdline_str:
                            pids[service] = proc.info['pid']
                            break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return pids

    def get_system_resources_panel(self):
        """This function is now fast. It only reads pre-collected data."""
        resources_table = Table(expand=True, show_header=True, header_style="bold blue")
        resources_table.add_column("Service", justify="left", style="cyan", min_width=12)
        resources_table.add_column("CPU, %", justify="center", min_width=6)
        resources_table.add_column("RAM, MB", justify="center", min_width=6)
        resources_table.add_column("VRAM, MB", justify="center", min_width=6)

        display_map = {'stt': 'Whisper', 'tts': 'Kokoro', 'Ollama': 'Ollama', 'App (Main)': 'App (Main)'}
        
        with self._lock:
            # Render from the collected self.system_resources
            for key, display_name in display_map.items():
                data = self.system_resources.get(key)
                if data:
                    cpu = f"{data.get('cpu', 0):.1f}"
                    ram = f"{data.get('ram', 0):.0f}"
                    vram = data.get('vram', '-')
                    resources_table.add_row(display_name, cpu, ram, str(vram))
                else:
                    resources_table.add_row(display_name, "offline", "offline", "-")

            status_table = Table.grid(padding=(0, 1))
            status_table.add_column(justify="right", style="bold green")
            status_table.add_column(justify="left", style="white")
            status_table.add_row("RMS Levels", self.audio_level)
            status_table.add_row("State", self.assistant_state)
            status_table.add_row("Intent", self.intent)

            top_grid = Table.grid(expand=True)
            top_grid.add_column(ratio=1)
            top_grid.add_column(ratio=1)
            top_grid.add_row(resources_table, Panel(status_table, title="Status", border_style="cyan"))

            return Panel(top_grid, title="Voice Assistant Dashboard", border_style="blue")

    def get_performance_panel(self):
        with self._lock:
            perf_text = " | ".join([f"{k}: {v}" for k, v in self.perf_metrics.items()])
        return Panel(Text(perf_text, justify="center"), title="Performance Metrics")

    def start(self):
        self.live.start()
        self.ui_thread.start()
        self.data_thread.start()

    def stop(self):
        self.stop_event.set()
        self.ui_thread.join()
        self.data_thread.join()
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
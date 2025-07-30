from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.text import Text
import psutil
import time
import threading

def get_gpu_usage():
    """Get GPU usage information from nvidia-smi if available."""
    import subprocess
    
    try:
        # Get GPU utilization and memory info
        result = subprocess.run([
            'nvidia-smi', '--query-gpu=utilization.gpu,memory.used,memory.total', 
            '--format=csv,noheader,nounits'
        ], capture_output=True, text=True, timeout=3)
        
        if result.returncode == 0:
            gpu_info = result.stdout.strip().split(', ')
            if len(gpu_info) >= 3:
                gpu_util = int(gpu_info[0])
                vram_used = int(gpu_info[1])
                vram_total = int(gpu_info[2])
                
                # For now, we'll assume all GPU usage is from Ollama
                # In a real implementation, you'd need to match processes
                return {
                    "Ollama": {"gpu": gpu_util, "vram": vram_used},
                    "Whisper": {"gpu": max(0, gpu_util - 20), "vram": vram_used // 3},
                    "Kokoro": {"gpu": 0, "vram": 0}
                }
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        pass
    
    # Fallback to placeholder data
    return {
        "Ollama": {"gpu": "-", "vram": "-"},
        "Whisper": {"gpu": "-", "vram": "-"},
        "Kokoro": {"gpu": "-", "vram": "-"}
    }

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
        app_cpu = psutil.Process().cpu_percent() / psutil.cpu_count()
        app_ram = psutil.Process().memory_info().rss / (1024 * 1024)
        resources_table.add_row("App (Main)", f"{app_cpu:.1f}", f"{app_ram:.0f}", "-", "-")
        resources_table.add_row("  └─ KWD", "(incl)", "", "", "")

        # GPU data
        gpu_data = get_gpu_usage()
        for service, data in gpu_data.items():
            resources_table.add_row(service, "-", "-", f"{data['gpu']}", f"{data['vram']}")

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

import zmq
import json
import time
import threading
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.text import Text
import psutil

class DashboardServiceV2:
    def __init__(self, port=5555):
        self.console = Console()
        self.port = port
        
        # ZeroMQ setup
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        self.socket.connect(f"tcp://localhost:{port}")
        self.socket.setsockopt_string(zmq.SUBSCRIBE, "")  # Subscribe to all messages
        
        # Dashboard data
        self._lock = threading.Lock()
        self.data = {
            "state": "Initializing",
            "intent": "N/A",
            "audio_level": "0.00 / 0.00",
            "stt_output": "",
            "llm_output": "",
            "performance": {},
            "system_resources": {}
        }
        
        # Rich components
        self.layout = self.make_layout()
        self.live = Live(self.layout, console=self.console, screen=True, 
                        redirect_stderr=False, vertical_overflow="visible")
        
        # Control threads
        self.stop_event = threading.Event()
        self.subscriber_thread = None
        self.update_thread = None
        
    def make_layout(self):
        """Create the dashboard layout"""
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
        
    def get_system_resources_panel(self):
        """Generate system resources panel"""
        resources_table = Table(expand=True, show_header=True, header_style="bold blue")
        resources_table.add_column("Service", justify="left", style="cyan", min_width=12)
        resources_table.add_column("CPU %", justify="center", min_width=6)
        resources_table.add_column("RAM MB", justify="center", min_width=7)
        resources_table.add_column("GPU %", justify="center", min_width=6)
        resources_table.add_column("VRAM MB", justify="center", min_width=8)
        
        # Get system resources from stored data or calculate live
        with self._lock:
            system_data = self.data.get("system_resources", {})
        
        # App (Main) - always live data
        try:
            app_process = psutil.Process()
            app_cpu = app_process.cpu_percent() / psutil.cpu_count()
            app_ram = app_process.memory_info().rss / (1024 * 1024)
            resources_table.add_row("App (Main)", f"{app_cpu:.1f}", f"{app_ram:.0f}", "-", "-")
        except psutil.NoSuchProcess:
            resources_table.add_row("App (Main)", "offline", "offline", "-", "-")
        
        # AI Services - from published data or defaults
        services = ["Whisper", "Kokoro", "Ollama"]
        for service in services:
            if service in system_data:
                data = system_data[service]
                resources_table.add_row(
                    service,
                    f"{data.get('cpu', 0):.1f}",
                    f"{data.get('ram', 0):.0f}",
                    f"{data.get('gpu', 0)}",
                    f"{data.get('vram', 0)}"
                )
            else:
                resources_table.add_row(service, "offline", "offline", "-", "-")
        
        return Panel(resources_table, title="System Resources")
        
    def get_status_panel(self):
        """Generate status panel with audio, state, intent"""
        with self._lock:
            status_table = Table.grid(padding=(0, 1))
            status_table.add_column(justify="right", style="bold green")
            status_table.add_column(justify="left", style="white")
            status_table.add_row("RMS Levels", self.data["audio_level"])
            status_table.add_row("State", self.data["state"])
            status_table.add_row("Intent", self.data["intent"])
        
        return Panel(status_table, title="Status", border_style="cyan")
        
    def get_performance_panel(self):
        """Generate performance metrics panel"""
        with self._lock:
            perf_data = self.data["performance"]
        
        perf_text = " | ".join([f"{k}: {v}" for k, v in perf_data.items()])
        return Panel(Text(perf_text, justify="center"), title="Performance Metrics")
        
    def update_layout(self):
        """Update the dashboard layout"""
        # Main header with system resources and status
        top_grid = Table.grid(expand=True)
        top_grid.add_column(ratio=2)  # System resources
        top_grid.add_column(ratio=1)  # Status
        
        system_panel = self.get_system_resources_panel()
        status_panel = self.get_status_panel()
        
        top_grid.add_row(system_panel, status_panel)
        main_header = Panel(top_grid, title="Voice Assistant Dashboard", border_style="blue")
        
        # Performance panel
        performance_panel = self.get_performance_panel()
        
        # STT and LLM output panels
        with self._lock:
            stt_panel = Panel(Text(self.data["stt_output"]), title="STT Output")
            llm_panel = Panel(Text(self.data["llm_output"]), title="LLM Output")
        
        # Update layout
        self.layout["main_header"].update(main_header)
        self.layout["performance"].update(performance_panel)
        self.layout["stt"].update(stt_panel)
        self.layout["llm"].update(llm_panel)
        
    def subscriber_loop(self):
        """Subscribe to ZeroMQ messages and update data"""
        while not self.stop_event.is_set():
            try:
                # Non-blocking receive with timeout
                if self.socket.poll(timeout=100):  # 100ms timeout
                    message = self.socket.recv_json(zmq.NOBLOCK)
                    self.process_message(message)
            except zmq.Again:
                # No message received, continue
                continue
            except Exception as e:
                print(f"Error receiving message: {e}")
                time.sleep(0.1)
                
    def process_message(self, message):
        """Process received message and update data"""
        if not isinstance(message, dict):
            return
            
        with self._lock:
            # Update data based on message type
            if "type" in message:
                msg_type = message["type"]
                
                if msg_type == "state":
                    self.data["state"] = message.get("value", "Unknown")
                elif msg_type == "intent":
                    self.data["intent"] = message.get("value", "N/A")
                elif msg_type == "audio_level":
                    self.data["audio_level"] = message.get("value", "0.00 / 0.00")
                elif msg_type == "stt_output":
                    self.data["stt_output"] = message.get("value", "")
                elif msg_type == "llm_output":
                    self.data["llm_output"] = message.get("value", "")
                elif msg_type == "performance":
                    self.data["performance"].update(message.get("value", {}))
                elif msg_type == "system_resources":
                    self.data["system_resources"].update(message.get("value", {}))
                    
    def update_loop(self):
        """Update dashboard display periodically"""
        while not self.stop_event.is_set():
            try:
                self.update_layout()
                time.sleep(0.5)  # Update every 500ms
            except Exception as e:
                print(f"Error updating layout: {e}")
                time.sleep(1)
                
    def start(self):
        """Start the dashboard service"""
        print("Starting dashboard service...")
        
        # Start the live display
        self.live.start()
        
        # Start subscriber thread
        self.subscriber_thread = threading.Thread(target=self.subscriber_loop, daemon=True)
        self.subscriber_thread.start()
        
        # Start update thread
        self.update_thread = threading.Thread(target=self.update_loop, daemon=True)
        self.update_thread.start()
        
        print("Dashboard service started")
        
    def stop(self):
        """Stop the dashboard service"""
        print("Stopping dashboard service...")
        
        # Signal threads to stop
        self.stop_event.set()
        
        # Wait for threads to finish
        if self.subscriber_thread:
            self.subscriber_thread.join(timeout=2)
        if self.update_thread:
            self.update_thread.join(timeout=2)
            
        # Stop live display
        self.live.stop()
        
        # Close ZeroMQ socket
        self.socket.close()
        self.context.term()
        
        print("Dashboard service stopped")
        
    def run(self):
        """Main run method - blocks until stopped"""
        try:
            self.start()
            # Keep running until interrupted
            while not self.stop_event.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nReceived interrupt signal")
        finally:
            self.stop()

if __name__ == "__main__":
    dashboard = DashboardServiceV2()
    dashboard.run()

import zmq
import time
import threading
from rich.live import Live
from services.dashboard_ui import DashboardUI

class DashboardService:
    def __init__(self, port=5555):
        # Initialize UI and ZeroMQ
        self.ui = DashboardUI()
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        self.socket.connect(f"tcp://localhost:{port}")
        self.socket.setsockopt_string(zmq.SUBSCRIBE, "")
        
        # Thread-safe data storage
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
        
        # Rich Live display
        self.layout = self.ui.create_layout()
        self.live = Live(self.layout, screen=True, redirect_stderr=False, vertical_overflow="visible")
        
        # Control threads
        self.stop_event = threading.Event()
        self.subscriber_thread = threading.Thread(target=self._subscriber_loop, daemon=True)
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)

    def _subscriber_loop(self):
        """Subscribe to ZeroMQ messages and update data"""
        while not self.stop_event.is_set():
            try:
                if self.socket.poll(timeout=100):
                    message = self.socket.recv_json(zmq.NOBLOCK)
                    with self._lock:
                        self.data.update(message)
            except zmq.Again:
                continue
            except Exception as e:
                # Log errors in a real application
                time.sleep(0.1)

    def _update_loop(self):
        """Update dashboard display periodically"""
        while not self.stop_event.is_set():
            try:
                with self._lock:
                    # Generate panels from UI configuration
                    main_header = self.ui.create_main_header_panel(
                        self.data["system_resources"],
                        self.data["audio_level"],
                        self.data["state"],
                        self.data["intent"]
                    )
                    performance_panel = self.ui.create_performance_panel(self.data["performance"])
                    stt_panel = self.ui.create_stt_panel(self.data["stt_output"])
                    llm_panel = self.ui.create_llm_panel(self.data["llm_output"])
                
                # Update layout with new panels
                self.layout["main_header"].update(main_header)
                self.layout["performance"].update(performance_panel)
                self.layout["stt"].update(stt_panel)
                self.layout["llm"].update(llm_panel)
                
                time.sleep(0.5)
            except Exception as e:
                # Log errors in a real application
                time.sleep(1)

    def start(self):
        self.live.start()
        self.subscriber_thread.start()
        self.update_thread.start()

    def stop(self):
        self.stop_event.set()
        self.subscriber_thread.join(timeout=1)
        self.update_thread.join(timeout=1)
        self.live.stop()
        self.socket.close()
        self.context.term()

    def run(self):
        try:
            self.start()
            while not self.stop_event.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

if __name__ == "__main__":
    dashboard = DashboardService()
    dashboard.run()

#!/usr/bin/env python3
"""
Lightweight memory logger stub to satisfy imports.
Can be expanded to track RSS/CPU over time if needed.
"""
import threading
import time
from typing import Optional

class MemoryLogger:
    def __init__(self, interval: float = 5.0):
        self.interval = interval
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()

    def _run(self):
        while not self._stop.is_set():
            # Placeholder for actual memory sampling
            time.sleep(self.interval)

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=self.interval * 2)


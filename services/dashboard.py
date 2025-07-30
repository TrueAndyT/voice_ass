import threading
import time
import sys
import shutil
import textwrap

class Dashboard:
    def __init__(self, update_interval=0.5):
        self.rms = "0.000"
        self.kwd_status = "Idle"
        self.vram_text = "0 MB / 0%"
        self.cpu_text = "0%"
        self.mode = "Idle"
        self.wakeword = "-"
        self.llm = ""
        self.stt = ""

        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._interval = update_interval
        self._thread = None
        self._drawn_once = False
        self._start_row = 3  # Fixed row for dashboard start

    def start(self):
        if not self._thread:
            self._thread = threading.Thread(target=self._render_loop, daemon=True)
            self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join()

    def update_rms(self, value: float):
        with self._lock:
            self.rms = f"{value:.3f}"

    def update_kwd(self, status: str):
        with self._lock:
            self.kwd_status = status

    def update_vram(self, used_mb: int, percent: int):
        with self._lock:
            self.vram_text = f"{used_mb} MB / {percent}%"

    def update_cpu(self, percent: float):
        with self._lock:
            self.cpu_text = f"{int(percent)}%"

    def update_mode(self, mode: str):
        with self._lock:
            self.mode = mode

    def update_wakeword(self, wakeword: str):
        with self._lock:
            self.wakeword = wakeword

    def update_llm(self, reply: str):
        with self._lock:
            self.llm = reply.strip()

    def update_stt(self, text: str):
        with self._lock:
            self.stt = text.strip()

    def _render_loop(self):
        while not self._stop_event.is_set():
            with self._lock:
                if not self._drawn_once:
                    self._render_static_frame()
                    self._drawn_once = True
                self._render_dynamic_content()
            time.sleep(self._interval)

    def _render_static_frame(self):
        width = shutil.get_terminal_size().columns
        blank = " " * (width - 2)
        lines = [
            "┏━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┓",
            "┃ DynRMS    ┃ KWD Status   ┃ VRAM Used / Total  ┃ CPU % ┃",
            "┃           ┃              ┃                    ┃       ┃",
            "┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫",
            f"┃ Mode:                │ Wakeword:                                                  ┃",
            "┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫",
        ]
        # 5 lines LLM, 5 lines STT
        lines += [f"┃ LLM: {blank}┃" for _ in range(5)]
        lines += [f"┃ STT: {blank}┃" for _ in range(5)]
        lines += ["┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛"]

        sys.stdout.write("\n" + "\n".join(lines) + "\n")
        sys.stdout.flush()

    def _render_dynamic_content(self):
        term_width = shutil.get_terminal_size().columns
        content_width = term_width - 8  # for borders/prefix
        def move(row): sys.stdout.write(f"\033[{self._start_row + row};1H")
        def clear(): sys.stdout.write("\033[2K")

        # Line 2 — values
        move(2); clear()
        sys.stdout.write(f"┃ {self.rms:<9} ┃ {self.kwd_status:<12} ┃ {self.vram_text:<18} ┃ {self.cpu_text:<5} ┃\n")

        # Line 4 — mode + wakeword
        move(4); clear()
        mode = f"Mode: {self.mode:<12}"
        wake = f"Wakeword: \"{self.wakeword}\""
        pad = term_width - len(mode) - len(wake) - 6
        sys.stdout.write(f"┃ {mode} │ {wake}{' ' * pad}┃\n")

        # LLM block
        llm_lines = textwrap.wrap(self.llm, width=content_width)
        for i in range(5):
            move(6 + i); clear()
            text = llm_lines[i] if i < len(llm_lines) else ""
            prefix = "LLM: " if i == 0 else "     "
            sys.stdout.write(f"┃ {prefix}{text:<{content_width}}┃\n")

        # STT block
        stt_lines = textwrap.wrap(self.stt, width=content_width)
        for i in range(5):
            move(11 + i); clear()
            text = stt_lines[i] if i < len(stt_lines) else ""
            prefix = "STT: " if i == 0 else "     "
            sys.stdout.write(f"┃ {prefix}{text:<{content_width}}┃\n")

        sys.stdout.flush()


# Global singleton
DASHBOARD = Dashboard()

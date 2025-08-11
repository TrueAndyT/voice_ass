#!/usr/bin/env python3
"""
Centralized logging utilities for the Voice Assistant.
Provides a singleton `app_logger` with:
- get_logger(name): configured Python logger
- log_performance(event, duration, context=None): JSONL performance log
- handle_exception(exc_type, exc_value, tb, context=None): structured exception logging
"""

import json
import logging
import os
import sys
import threading
import traceback
from datetime import datetime
from typing import Any, Dict, Optional

_LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "logs")
_LOG_DIR = os.path.abspath(_LOG_DIR)
_APP_LOG = os.path.join(_LOG_DIR, "app.jsonl")
_PERF_LOG = os.path.join(_LOG_DIR, "performance.jsonl")

class _ColorFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: "\033[36m",   # Cyan
        logging.INFO: "\033[32m",    # Green
        logging.WARNING: "\033[33m", # Yellow
        logging.ERROR: "\033[31m",   # Red
        logging.CRITICAL: "\033[35m" # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelno, "")
        msg = super().format(record)
        if sys.stderr.isatty():
            return f"{color}{msg}{self.RESET}"
        return msg

class AppLogger:
    def __init__(self):
        self._init_once_lock = threading.Lock()
        self._initialized = False
        self._jsonl_handler = None
        self._console_handler = None
        self._ensure_initialized()

    def _ensure_initialized(self):
        with self._init_once_lock:
            if self._initialized:
                return
            os.makedirs(_LOG_DIR, exist_ok=True)

            # Structured JSON file handler for app logs
            self._jsonl_handler = logging.FileHandler(_APP_LOG, encoding="utf-8")
            self._jsonl_handler.setLevel(logging.DEBUG)
            self._jsonl_handler.setFormatter(logging.Formatter('%(message)s'))

            # Console handler for human-readable output
            self._console_handler = logging.StreamHandler(sys.stdout)
            self._console_handler.setLevel(logging.INFO)
            self._console_handler.setFormatter(_ColorFormatter('[%(levelname)s] %(name)s: %(message)s'))

            self._initialized = True

    def get_logger(self, name: str) -> logging.Logger:
        self._ensure_initialized()
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)

        # Avoid adding duplicate handlers
        needs_jsonl = all(not isinstance(h, logging.FileHandler) or h.baseFilename != os.path.abspath(_APP_LOG)
                          for h in logger.handlers)
        needs_console = all(not isinstance(h, logging.StreamHandler) for h in logger.handlers)

        if needs_jsonl and self._jsonl_handler:
            logger.addHandler(self._jsonl_handler)
        if needs_console and self._console_handler:
            logger.addHandler(self._console_handler)

        # Ensure file output is JSONL by wrapping log records
        original_makeRecord = logger.makeRecord
        def makeRecord(name, level, fn, lno, msg, args, exc_info, func=None, extra=None, sinfo=None):
            # For file handler, we want JSON lines; for console, keep human-readable
            # We serialize in the emit step by converting message to JSON string for file handler
            return original_makeRecord(name, level, fn, lno, msg, args, exc_info, func, extra, sinfo)
        logger.makeRecord = makeRecord  # type: ignore

        # Add filter to convert records to JSON for the file handler only
        class JsonlFilter(logging.Filter):
            def filter(self, record: logging.LogRecord) -> bool:
                # Build JSON structure
                payload: Dict[str, Any] = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "level": record.levelname,
                    "name": record.name,
                    "message": record.getMessage(),
                }
                # Include structured props when provided via `extra={"props": {...}}`
                props = getattr(record, "props", None)
                if isinstance(props, dict):
                    payload["props"] = props
                # Stash JSON string in record.message for file handler
                record.msg = json.dumps(payload, ensure_ascii=False)
                record.args = ()
                return True

        # Ensure the file handler uses JSONL filter while console stays human-readable
        if self._jsonl_handler and JsonlFilter not in [type(f) for f in self._jsonl_handler.filters]:
            self._jsonl_handler.addFilter(JsonlFilter())

        return logger

    def log_performance(self, event: str, duration: float, context: Optional[Dict[str, Any]] = None):
        self._ensure_initialized()
        os.makedirs(_LOG_DIR, exist_ok=True)
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": event,
            "duration": duration,
        }
        if context:
            entry["context"] = context
        try:
            with open(_PERF_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:
            # Fall back to stderr if file write fails
            print(f"[PERF] {entry}")

    def handle_exception(self, exc_type, exc_value, tb, context: Optional[Dict[str, Any]] = None):
        log = self.get_logger("exceptions")
        trace_str = "".join(traceback.format_exception(exc_type, exc_value, tb))
        payload = {
            "exception_type": getattr(exc_type, "__name__", str(exc_type)),
            "message": str(exc_value),
            "traceback": trace_str,
        }
        if context:
            payload["context"] = context
        log.error("Unhandled exception", extra={"props": payload})

# Singleton instance
app_logger = AppLogger()


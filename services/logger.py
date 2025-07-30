import logging
import logging.config
import os
import sys
import json
import traceback
from datetime import datetime

# ---
# Filter to remove ANSI color codes from log records
# ---
class ColorFilter(logging.Filter):
    def filter(self, record):
        # Remove ANSI color codes from all string fields
        import re
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        
        record.levelname = ansi_escape.sub('', record.levelname).strip()
        record.name = ansi_escape.sub('', record.name).strip()
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            record.msg = ansi_escape.sub('', record.msg)
        return True

# ---
# Custom formatter for structured JSON logging
# ---
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, 'props'):
            log_record.update(record.props)
        return json.dumps(log_record)

# ---
# Custom formatter for colored console output
# ---
class ColorFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": "\033[94m",    # Blue
        "INFO": "\033[92m",     # Green
        "WARNING": "\033[93m", # Yellow
        "ERROR": "\033[91m",    # Red
        "CRITICAL": "\033[95m",# Magenta
        "RESET": "\033[0m",
    }

    def format(self, record):
        color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
        record.levelname = f"{color}{record.levelname.ljust(8)}{self.COLORS['RESET']}"
        record.name = f"\033[96m{record.name.ljust(20)}\033[0m" # Cyan, aligned to microservices_loader
        return super().format(record)


class AppLogger:
    _instance = None
    _loggers = {}

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(AppLogger, cls).__new__(cls)
        return cls._instance

    def __init__(self, log_dir="logs", console_level=logging.INFO, file_level=logging.DEBUG):
        if hasattr(self, '_initialized') and self._initialized:
            return
        self._initialized = True
        
        self.log_dir = log_dir
        self.console_level = console_level
        self.file_level = file_level
        self.log_file = os.path.join(self.log_dir, "app.jsonl")

        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir, exist_ok=True)

        # Performance timers log
        self.perf_log_file = os.path.join(self.log_dir, "performance.jsonl")

    def get_logger(self, name="main"):
        if name in self._loggers:
            return self._loggers[name]

        logger = logging.getLogger(name)
        logger.setLevel(self.file_level)
        logger.propagate = False

        if not logger.handlers:
            # Console handler with colors
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self.console_level)
            console_format = ColorFormatter("%(name)s - %(levelname)s - %(message)s")
            console_handler.setFormatter(console_format)
            logger.addHandler(console_handler)

            # JSON file handler (no colors)
            file_handler = logging.FileHandler(self.log_file)
            file_handler.setLevel(self.file_level)
            file_handler.addFilter(ColorFilter())  # Remove color codes from file logs
            file_handler.setFormatter(JsonFormatter())
            logger.addHandler(file_handler)

        self._loggers[name] = logger
        return logger

    def handle_exception(self, exc_type, exc_value, exc_traceback, logger_name="main", context=None):
        logger = self.get_logger(logger_name)
        
        # Construct structured log context
        props = {
            "exception_type": exc_type.__name__,
            "traceback": ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback)),
            "context": context or {},
        }

        # Log the critical error
        logger.critical(f"{exc_value}", extra={"props": props})

        # Also log to console for immediate visibility during development
        print(f"\nCRITICAL ERROR: {exc_value}\nTraceback:\n{''.join(traceback.format_tb(exc_traceback))}", file=sys.stderr)

    def log_performance(self, event: str, duration: float, context: dict = None):
        perf_record = {
            "timestamp": datetime.now().isoformat(),
            "event": event,
            "duration_ms": round(duration * 1000, 2),
            "context": context or {}
        }
        with open(self.perf_log_file, 'a') as f:
            f.write(json.dumps(perf_record) + '\n')

# ---
# Singleton instance of the logger
# ---
app_logger = AppLogger()

# ---
# Backward compatibility function
# ---
def setup_logging(log_file=None, log_level=logging.INFO):
    """
    Backward compatibility function for existing code.
    Returns the main logger from the new system.
    """
    return app_logger.get_logger("main")

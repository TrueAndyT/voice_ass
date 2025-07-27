import logging
import os

LOG_FILE = os.path.join("logs", "wakeword.log")

def setup_logger():
    """Sets up a logger to write to logs/wakeword.log."""
    log_dir = os.path.dirname(LOG_FILE)
    os.makedirs(log_dir, exist_ok=True)
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s.%(msecs)s | %(message)s',
        datefmt='%H:%M:%S',
        filename=LOG_FILE,
        filemode='w'
    )
    return logging.getLogger("wakeword")
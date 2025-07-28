import logging
from logging.handlers import RotatingFileHandler
import os
import sys
import time

def setup_logging(log_file=os.path.join('logs', 'app.log'), log_level=logging.INFO): # <-- MODIFIED
    """
    Sets up a rotating logger.
    """
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger()
    logger.setLevel(log_level)

    logger.propagate = False

    if logger.hasHandlers():
        logger.handlers.clear()

    # Configure the formatter to use the system's local time
    log_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    log_format.converter = time.localtime

    # Console handler
    c_handler = logging.StreamHandler(sys.stdout)
    c_handler.setFormatter(log_format)
    logger.addHandler(c_handler)

    # File handler with rotation
    f_handler = RotatingFileHandler(log_file, maxBytes=1024*1024*5, backupCount=5)
    f_handler.setFormatter(log_format)
    logger.addHandler(f_handler)

    return logger
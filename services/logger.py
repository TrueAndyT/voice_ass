import logging
from logging.handlers import RotatingFileHandler
import os
import sys
import time # <-- Import the time module

def setup_logging(log_file='app.log', log_level=logging.INFO):
    """
    Sets up a rotating logger.
    """
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger = logging.getLogger()
    logger.setLevel(log_level)

    logger.propagate = False

    if logger.hasHandlers():
        logger.handlers.clear()

    # --- MODIFIED FORMATTER ---
    # Configure the formatter to use the system's local time
    log_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    log_format.converter = time.localtime
    # --- END OF MODIFICATION ---

    # Console handler
    c_handler = logging.StreamHandler(sys.stdout)
    c_handler.setFormatter(log_format) # Use the corrected formatter
    logger.addHandler(c_handler)

    # File handler with rotation
    f_handler = RotatingFileHandler(log_file, maxBytes=1024*1024*5, backupCount=5)
    f_handler.setFormatter(log_format) # Use the corrected formatter
    logger.addHandler(f_handler)

    return logger
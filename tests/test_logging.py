#!/usr/bin/env python3
"""Test script to verify logging configuration."""

from services.utils.logger import app_logger

# Test different loggers
main_log = app_logger.get_logger("main")
loader_log = app_logger.get_logger("microservices_loader")
client_log = app_logger.get_logger("tts_client")

# Test different log levels
main_log.debug("This is a DEBUG message - should only appear in file")
main_log.info("This is an INFO message - should appear in console and file")
main_log.warning("This is a WARNING message - should appear in console and file")
main_log.error("This is an ERROR message - should appear in console and file")

loader_log.debug("Loader DEBUG - file only")
loader_log.info("Loader INFO - console and file")

client_log.debug("Client DEBUG - file only")
client_log.info("Client INFO - console and file")

print("\nCheck logs folder for app.jsonl and performance.jsonl files")

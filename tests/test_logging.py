#!/usr/bin/env python3
"""
Test script to verify the enhanced logging system works correctly.
"""

import time
import traceback
import sys
import os

# Add parent directory to path so we can import services
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.logger import app_logger
from services.exceptions import VoiceAssistantException, STTException

def test_basic_logging():
    """Test basic logging functionality with colors."""
    print("=== Testing Basic Logging ===")
    
    # Get loggers for different services
    main_log = app_logger.get_logger("main")
    stt_log = app_logger.get_logger("stt_service")
    llm_log = app_logger.get_logger("llm_service")
    
    # Test different log levels
    main_log.debug("This is a debug message")
    main_log.info("Voice Assistant starting up...")
    main_log.warning("This is a warning message")
    main_log.error("This is an error message")
    
    stt_log.info("Speech-to-text service initialized")
    llm_log.info("Language model loaded successfully")
    
    print("✓ Basic logging test completed")

def test_performance_logging():
    """Test performance metrics logging."""
    print("\n=== Testing Performance Logging ===")
    
    # Simulate some operations with timing
    start_time = time.time()
    time.sleep(0.1)  # Simulate work
    duration = time.time() - start_time
    
    app_logger.log_performance(
        "test_operation",
        duration,
        {"input_size": 100, "output_size": 50}
    )
    
    app_logger.log_performance(
        "model_warmup",
        0.5,
        {"stt": 0.2, "llm": 0.3}
    )
    
    print("✓ Performance logging test completed")

def test_exception_handling():
    """Test exception handling and logging."""
    print("\n=== Testing Exception Handling ===")
    
    # Test custom exception handling
    try:
        raise STTException(
            "Failed to transcribe audio",
            context={"device": "cuda", "model": "whisper-small"},
            recoverable=True
        )
    except VoiceAssistantException as e:
        app_logger.handle_exception(
            type(e), e, e.__traceback__,
            logger_name="stt_service",
            context={"test": "exception_handling"}
        )
    
    # Test regular exception handling
    try:
        raise ValueError("This is a test error")
    except Exception as e:
        app_logger.handle_exception(
            type(e), e, e.__traceback__,
            logger_name="main",
            context={"test": "regular_exception"}
        )
    
    print("✓ Exception handling test completed")

def test_structured_logging():
    """Test structured logging with context."""
    print("\n=== Testing Structured Logging ===")
    
    log = app_logger.get_logger("test")
    
    # Log with structured context
    log.info("Processing user request", extra={
        "props": {
            "user_input": "test query",
            "intent": "general",
            "response_time_ms": 150
        }
    })
    
    log.error("Service failed to respond", extra={
        "props": {
            "service": "llm_service",
            "error_code": "TIMEOUT",
            "retry_count": 3
        }
    })
    
    print("✓ Structured logging test completed")

def main():
    """Run all logging tests."""
    print("🧪 Testing Enhanced Logging System")
    print("=" * 50)
    
    try:
        test_basic_logging()
        test_performance_logging()
        test_exception_handling()
        test_structured_logging()
        
        print("\n" + "=" * 50)
        print("✅ All logging tests passed!")
        print("\nCheck the following files:")
        print("  📄 logs/app.jsonl - Structured JSON logs")
        print("  📊 logs/performance.jsonl - Performance metrics")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Comprehensive test runner for all Voice Assistant tests.

This script runs all available tests and provides a summary of results.
"""

import sys
import os
import subprocess
import importlib.util

# Add parent directory to path so we can import services
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.logger import app_logger

def run_test_script(script_path, script_name):
    """Run a test script and return success status."""
    log = app_logger.get_logger("test_runner")
    
    try:
        log.info(f"Running {script_name}...")
        
        # Import and run the test module
        spec = importlib.util.spec_from_file_location(script_name, script_path)
        module = importlib.util.module_from_spec(spec)
        
        # Capture stdout to check for errors
        import io
        from contextlib import redirect_stdout, redirect_stderr
        
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            spec.loader.exec_module(module)
        
        stdout_output = stdout_capture.getvalue()
        stderr_output = stderr_capture.getvalue()
        
        # Print the captured output
        if stdout_output:
            print(stdout_output)
        if stderr_output:
            print(stderr_output, file=sys.stderr)
        
        # Check for test failures
        if "❌" in stdout_output or "failed" in stderr_output.lower():
            log.warning(f"{script_name} completed with some failures")
            return False
        else:
            log.info(f"{script_name} completed successfully")
            return True
            
    except Exception as e:
        log.error(f"Error running {script_name}: {e}")
        return False

def main():
    """Run all tests and provide summary."""
    log = app_logger.get_logger("test_runner")
    
    print("🧪 Running All Voice Assistant Tests")
    print("=" * 60)
    
    tests_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define test scripts to run
    test_scripts = [
        ("test_logging.py", "Logging System Tests"),
        ("test_services.py", "Service Framework Tests"),
        # Note: Microservices test requires services to be running
        # ("test_microservices.py", "Microservices Architecture Tests"),
    ]
    
    results = []
    
    for script_file, description in test_scripts:
        script_path = os.path.join(tests_dir, script_file)
        
        if os.path.exists(script_path):
            print(f"\n📋 {description}")
            print("-" * 40)
            success = run_test_script(script_path, script_file)
            results.append((description, success))
        else:
            log.warning(f"Test script not found: {script_path}")
            results.append((description, False))
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name:<40} {status}")
        if success:
            passed += 1
    
    print("-" * 60)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        log.info("All tests completed successfully")
    else:
        print(f"⚠️  {total - passed} test(s) failed")
        log.warning(f"{total - passed} test(s) failed")
    
    print("\n📄 Log files:")
    print("  • logs/app.jsonl - Structured application logs")
    print("  • logs/performance.jsonl - Performance metrics")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

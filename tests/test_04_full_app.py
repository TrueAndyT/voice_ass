#!/usr/bin/env python3
"""
Test 4: Full Application Test
Runs the main application with detailed logging to pinpoint the segmentation fault.
"""

import subprocess
import sys
import time
import threading


def run_full_app_test():
    print("\n=== Test 4: Full Application Test ===")
    main_proc = None
    
    def run_main():
        nonlocal main_proc
        command = [sys.executable, "main.py"]
        main_proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Capture and print stdout/stderr in real-time
        for line in iter(main_proc.stdout.readline, ''):
            print(f"[main.py] {line.strip()}")
        for line in iter(main_proc.stderr.readline, ''):
            print(f"[main.py E] {line.strip()}")

    try:
        print("1. Starting main application in a separate thread...")
        main_thread = threading.Thread(target=run_main)
        main_thread.start()
        
        print("2. Waiting for 15 seconds to see if a crash occurs...")
        main_thread.join(timeout=15)
        
        if main_thread.is_alive():
            print("   Main application still running ✓")
            result = "PASSED"
        else:
            print("   Main application crashed ❌")
            result = "FAILED"

    finally:
        if main_proc and main_proc.poll() is None:
            print("\n--- Cleaning up main application ---")
            main_proc.terminate()
            main_proc.wait()
            print("   Main application stopped ✓")
    
    if result == "PASSED":
        print("\n🎉 Test 4 PASSED: Main application ran without crashing.")
    else:
        print("\n❌ Test 4 FAILED: Main application crashed.")

if __name__ == "__main__":
    run_full_app_test()


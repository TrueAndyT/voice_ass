#!/usr/bin/env python3
"""
Runs all test scripts in sequence to provide a comprehensive diagnostic.
"""

import subprocess
import sys

TEST_SCRIPTS = [
    "test_01_pyaudio_basic.py",
    "test_02_kwd_service.py",
    "test_03_microservices.py",
]

def run_all_tests():
    print("====== RUNNING ALL TESTS ======")
    all_passed = True
    
    for script in TEST_SCRIPTS:
        print(f"\n--- Running: {script} ---")
        try:
            result = subprocess.run(
                [sys.executable, script],
                capture_output=True,
                text=True,
                check=True,  # Raise an exception if the script returns a non-zero exit code
            )
            print(result.stdout)
            if "FAILED" in result.stdout:
                all_passed = False
                print(f"--- {script}: FAILED ---")
            else:
                print(f"--- {script}: PASSED ---")
        except subprocess.CalledProcessError as e:
            all_passed = False
            print(f"--- {script}: FAILED (crashed) ---")
            print(e.stdout)
            print(e.stderr)
        except FileNotFoundError:
            all_passed = False
            print(f"--- {script}: FAILED (file not found) ---")
            
    print("\n====== TEST SUMMARY ======")
    if all_passed:
        print("🎉 All tests passed!")
    else:
        print("❌ One or more tests failed.")

if __name__ == "__main__":
    run_all_tests()


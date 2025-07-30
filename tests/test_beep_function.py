#!/usr/bin/env python3

import subprocess
import threading
import time

def play_beep(sound_type="ready", log=None):
    """Play a short, pleasant system sound to indicate system readiness."""
    def _beep():
        try:
            # Use local WAV files
            base_path = "/home/master/Projects/test/config/sounds"
            if sound_type == "ready":
                sound_file = f"{base_path}/ready.wav"
            else:  # sound_type == "end"
                sound_file = f"{base_path}/end.wav"
            
            print(f"Trying to play: {sound_file}")
            
            # Try multiple methods
            methods = [
                f"paplay {sound_file}",
                f"aplay -q {sound_file}",
                f"play {sound_file} 2>/dev/null" if subprocess.run("which play", shell=True, capture_output=True).returncode == 0 else None
            ]
            
            for method in methods:
                if method is None:
                    continue
                try:
                    print(f"  Trying: {method}")
                    result = subprocess.run(method, shell=True, timeout=3, capture_output=True, text=True)
                    print(f"  Result: {result.returncode}")
                    if result.stderr:
                        print(f"  Error: {result.stderr}")
                    if result.returncode == 0:
                        print(f"  Success with: {method}")
                        return
                except Exception as e:
                    print(f"  Exception with {method}: {e}")
            
            print("All audio methods failed, trying system beep...")
            
        except Exception as e:
            print(f"Could not play system sound: {e}")
        
        # Fallback to system beep
        try:
            print("Trying system beep...")
            # Multiple beep methods
            beep_methods = [
                "echo -e '\a'",
                "printf '\a'",
                "beep -f 800 -l 100" if subprocess.run("which beep", shell=True, capture_output=True).returncode == 0 else None
            ]
            
            for method in beep_methods:
                if method is None:
                    continue
                try:
                    subprocess.run(method, shell=True, timeout=1)
                    print(f"System beep with: {method}")
                    return
                except:
                    continue
                    
        except Exception as e2:
            print(f"Could not play system beep: {e2}")
        
        print("All sound methods failed!")
    
    # Run beep without threading first to see output
    _beep()

def test_beep_function():
    print("=== Testing Beep Function ===")
    
    print("\n1. Testing ready sound...")
    play_beep("ready")
    time.sleep(2)
    
    print("\n2. Testing end sound...")
    play_beep("end")
    time.sleep(2)
    
    print("\n3. Testing direct paplay...")
    try:
        result = subprocess.run("paplay /usr/share/sounds/LinuxMint/stereo/button-toggle-on.ogg", 
                              shell=True, timeout=3, capture_output=True, text=True)
        print(f"Direct paplay result: {result.returncode}")
        print(f"stdout: {result.stdout}")
        print(f"stderr: {result.stderr}")
    except Exception as e:
        print(f"Direct paplay failed: {e}")
    
    print("\n4. Testing system bell...")
    print("\\a", end='', flush=True)
    
    print("\nTest completed!")

if __name__ == "__main__":
    test_beep_function()

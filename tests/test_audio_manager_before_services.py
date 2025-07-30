import pyaudio
import time
import numpy as np
import sys
import os

# Add the project root to the path at the beginning to ensure we use local services
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import audio_stream_manager

# Audio settings
CHUNK = 480  # 30ms at 16kHz
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
RECORD_SECONDS = 5

def run_test():
    try:
        print("Testing audio stream manager BEFORE loading services...")
        
        # Test audio stream manager without any services loaded
        with audio_stream_manager(
            FORMAT, 
            CHANNELS, 
            RATE, 
            CHUNK
        ) as stream:
            
            print("Audio stream opened successfully. Reading audio for 5 seconds...")
            
            start_time = time.time()
            while time.time() - start_time < RECORD_SECONDS:
                audio_chunk = stream.read(CHUNK, exception_on_overflow=False)
                time.sleep(0.001)  # Small delay

        print("Test finished successfully.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    run_test()

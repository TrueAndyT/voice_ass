
import pyaudio
import time
import numpy as np

# Audio settings
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
RECORD_SECONDS = 5

def run_test():
    p = pyaudio.PyAudio()

    try:
        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK)

        print("Stream opened successfully. Recording for 5 seconds...")

        for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            data = stream.read(CHUNK)
            # You can optionally process the data here, e.g., convert to numpy array
            # frame = np.frombuffer(data, dtype=np.int16)

        print("Recording finished.")

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        if 'stream' in locals() and stream.is_active():
            stream.stop_stream()
            stream.close()
        p.terminate()
        print("PyAudio terminated.")

if __name__ == "__main__":
    run_test()


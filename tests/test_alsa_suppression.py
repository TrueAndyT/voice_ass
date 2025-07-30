
import pyaudio
import time
from ctypes import CFUNCTYPE, c_char_p, c_int, cdll

# Suppress ALSA, JACK, and PulseAudio warnings for cleaner output
ERROR_HANDLER_FUNC = CFUNCTYPE(None, c_char_p, c_int, c_char_p, c_int, c_char_p)

def py_error_handler(filename, line, function, err, fmt):
    pass

c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)

try:
    asound = cdll.LoadLibrary('libasound.so')
    asound.snd_lib_error_set_handler(c_error_handler)
except OSError:
    pass

# Also suppress JACK warnings
try:
    jack = cdll.LoadLibrary('libjack.so')
    jack.jack_set_error_function(c_error_handler)
except (OSError, AttributeError):
    pass

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


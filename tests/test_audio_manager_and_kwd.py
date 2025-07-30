
import pyaudio
import time
import numpy as np
import sys
import os

# Add the project root to the path at the beginning to ensure we use local services
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now import from the local services package
import services.microservices_loader as ml
import services.kwd_service as kwd
from main import audio_stream_manager

# Audio settings
CHUNK = 480  # 30ms at 16kHz
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
RECORD_SECONDS = 10

def run_test():
    service_manager = None
    try:
        # Load services
        print("Loading services...")
        vad, oww_model, stt_service, llm_service, tts_service, dynamic_rms, service_manager = ml.load_services_microservices()
        kwd_service = kwd.KWDService(oww_model, vad, dynamic_rms)
        print("Services loaded.")

        # Main application loop with audio stream management
        with audio_stream_manager(
            FORMAT, 
            CHANNELS, 
            RATE, 
            CHUNK
        ) as stream:
            
            print("Main application loop started. Running for 10 seconds...")
            
            start_time = time.time()
            while time.time() - start_time < RECORD_SECONDS:
                audio_chunk = stream.read(CHUNK, exception_on_overflow=False)
                dynamic_rms.update_threshold(audio_chunk)
                prediction, utterance_buffer = kwd_service.process_audio(audio_chunk)

                if prediction:
                    print(f"Wake word detected: {prediction}")

        print("Test finished successfully.")

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        if service_manager:
            service_manager.stop_all_services()
        print("Cleanup complete.")

if __name__ == "__main__":
    run_test()


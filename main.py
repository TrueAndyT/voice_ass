import pyaudio
import sys
import logging
from datetime import datetime
import time
import subprocess

# Import from the services package
from services.loader import load_services
from services.kwd_service import KWDService
from services.logger import setup_logging
from services.memory_logger import MemoryLogger # <-- Import the new service

def main():
    # --- Performance Timers ---
    app_start_time = time.time()

    # --- Configuration ---
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    VAD_FRAME_SAMPLES = int(RATE * (30 / 1000.0))
    WAKEWORD_THRESHOLD = 0.5
    
    log = setup_logging()
    mem_logger = MemoryLogger()
    
    try:
        mem_logger.start() # <-- Start VRAM logging

        # Load all services
        log.info("--- Loading all services ---")
        vad, oww_model, stt_service, llm_service, tts_service = load_services()
        kwd_service = KWDService(oww_model, vad)

        # --- T1: App Start to KWD Ready ---
        kwd_ready_time = time.time()
        log.info(f"--- Models loaded. Time to KWD ready: {kwd_ready_time - app_start_time:.2f} seconds ---")
        
        tts_service.speak("Hi Master! Alexa at your services.")

    except Exception as e:
        log.error(f"Failed to load services: {e}", exc_info=True)
        print(f"[ERROR] Failed to load services: {e}")
        mem_logger.stop() # Ensure logger stops on error
        return

    pa = pyaudio.PyAudio()
    stream = None
    try:
        stream = pa.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=VAD_FRAME_SAMPLES)
    except OSError as e:
        log.error(f"Could not open microphone stream: {e}", exc_info=True)
        print(f"\n[ERROR] Could not open microphone stream: {e}")
        return

    log.info("--- Main application loop started ---")
    print("\n--- Waiting for wake word ---")

    try:
        while True:
            audio_chunk = stream.read(VAD_FRAME_SAMPLES, exception_on_overflow=False)
            prediction, utterance_buffer = kwd_service.process_audio(audio_chunk)

            if prediction:
                top_wakeword = max(prediction, key=prediction.get)
                top_score = prediction[top_wakeword]

                if top_score >= WAKEWORD_THRESHOLD:
                    log.info(f"--- Actionable wake word detected: {top_wakeword} (Score: {top_score:.2f}) ---")
                    
                    stream.stop_stream()

                    print(f'\n🎙️  Wake word "{top_wakeword.replace("_v0.1.onnx", "")}" detected, listening for command...')
                    transcription = stt_service.listen_and_transcribe(timeout_ms=3000)
                    
                    if transcription:
                        speech_end_time = time.time()
                        print(f'🗣️  Transcription: "{transcription}"')
                        
                        # --- T2 & T3 Timer Start ---
                        llm_start_time = time.time()
                        llm_response = llm_service.get_response(transcription)
                        llm_end_time = time.time()
                        
                        tts_start_time = time.time()
                        print(f"🤖 LLM Response: {llm_response}")
                        tts_service.speak(llm_response)
                        
                        # --- Log Performance Timers ---
                        log.info(f"--- Time to LLM response: {llm_end_time - llm_start_time:.2f} seconds ---")
                        log.info(f"--- Time from speech end to TTS start: {tts_start_time - speech_end_time:.2f} seconds ---")

                        while True:
                            print("\nListening for follow-up...")
                            follow_up = stt_service.listen_and_transcribe(timeout_ms=4000)
                            speech_end_time = time.time()
                            
                            if follow_up:
                                print(f'🗣️  Transcription: "{follow_up}"')
                                llm_start_time = time.time()
                                llm_response = llm_service.get_response(follow_up)
                                llm_end_time = time.time()

                                tts_start_time = time.time()
                                print(f"🤖 LLM Response: {llm_response}")
                                tts_service.speak(llm_response)

                                log.info(f"--- Time to LLM response: {llm_end_time - llm_start_time:.2f} seconds ---")
                                log.info(f"--- Time from speech end to TTS start: {tts_start_time - speech_end_time:.2f} seconds ---")
                            else:
                                print("\nDialog ended due to inactivity.")
                                break
                    else:
                        log.info("STT service returned no transcription.")
                        print("No transcription was returned.")

                    stream.start_stream() 
                    kwd_service.enter_cooldown()
                    print("\n--- Waiting for wake word ---")

    except KeyboardInterrupt:
        print(f"\n🛑 [{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] --- Stopping ---")
    finally:
        if stream and stream.is_active():
            stream.stop_stream()
            stream.close()
        pa.terminate()
        
        mem_logger.stop() # <-- Stop VRAM logging
        log.info("--- Resources released ---")
        logging.shutdown()

if __name__ == '__main__':
    main()
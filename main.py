import pyaudio
import sys
import logging
from datetime import datetime

# Import from the services package
from services.logger import setup_logger
from services.loader import load_services
from services.wakeword import WakeWordService

# --- Configuration ---
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
VAD_FRAME_SAMPLES = int(RATE * (30 / 1000.0))

def main():
    log = setup_logger()
    
    try:
        vad, oww_model, stt_service, llm_service = load_services()
        kwd_service = WakeWordService(oww_model, vad)
    except Exception as e:
        log.error(f"Failed to load services: {e}", exc_info=True)
        print(f"[ERROR] Failed to load services: {e}")
        return

    pa = pyaudio.PyAudio()
    stream = None
    try:
        stream = pa.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=VAD_FRAME_SAMPLES)
    except OSError as e:
        log.error(f"Could not open microphone stream: {e}")
        print(f"\n[ERROR] Could not open microphone stream: {e}")
        return

    log.info("--- Main application loop started ---")

    try:
        while True:
            audio_chunk = stream.read(VAD_FRAME_SAMPLES, exception_on_overflow=False)
            prediction, utterance_buffer = kwd_service.process_audio(audio_chunk)

            if prediction:
                detected = False
                for model_name, score in prediction.items():
                    if score > 0.5:
                        detected = True
                        keyword = model_name.split('/')[-1].split('_')[1].capitalize()
                        log.info(f"✅ WAKEWORD DETECTED: {keyword} (Score: {score:.2f})")
                        print(f"✅ [{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Successfully detected {keyword}")
                        
                        # --- Enter Conversation Flow ---
                        stream.stop_stream()
                        
                        # Transcribe the initial command with a 2-second timeout
                        transcription = stt_service.listen_and_transcribe(timeout_ms=2000)
                        
                        if transcription:
                            print(f'🗣️ Transcription: "{transcription}"')
                            llm_response = llm_service.get_response(transcription)
                            print(f"🤖 LLM Response: {llm_response}")

                            # Enter the Dialog Loop
                            print("\n🔄 Entering dialog mode. Listening for your response...")
                            while True:
                                # Listen for a follow-up with a 4-second fallback timeout
                                follow_up = stt_service.listen_and_transcribe(timeout_ms=4000)
                                
                                if follow_up:
                                    print(f'🗣️ Transcription: "{follow_up}"')
                                    llm_response = llm_service.get_response(follow_up)
                                    print(f"🤖 LLM Response: {llm_response}")
                                else:
                                    # Timeout occurred, exit dialog
                                    print("\nDialog ended due to inactivity.")
                                    break
                        else:
                            log.info("STT service returned no transcription.")
                            print("No transcription was returned.")

                        # Restart the main KWD stream and let the service handle cooldown
                        stream.start_stream() 
                        kwd_service.enter_cooldown()
                        break 
                
                if not detected:
                    log.info("--- No wakeword detected. Returning to listen state. ---")
                        
    except KeyboardInterrupt:
        print(f"\n🛑 [{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] --- Stopping ---")
    finally:
        if stream and stream.is_active():
            stream.stop_stream()
            stream.close()
        pa.terminate()
        log.info("--- Resources released ---")
        logging.shutdown()

if __name__ == '__main__':
    main()
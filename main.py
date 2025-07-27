import pyaudio
import sys
import logging
from datetime import datetime
import subprocess

# Import from the services package
from services.loader import load_services
from services.wakeword import WakeWordService
from services.logger import setup_logger

def main():
    # --- Configuration ---
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    VAD_FRAME_SAMPLES = int(RATE * (30 / 1000.0))
    WAKEWORD_THRESHOLD = 0.5 # Confidence threshold for detection
    # --- End Configuration ---

    log = setup_logger()
    
    try:
        # Load all services
        vad, oww_model, stt_service, llm_service, tts_service = load_services()
        kwd_service = WakeWordService(oww_model, vad)

        # Use the TTS service to give a welcome message
        tts_service.speak("Hi Master! Miss Heart at your services.")

    except Exception as e:
        log.error(f"Failed to load services: {e}", exc_info=True)
        print(f"[ERROR] Failed to load services: {e}")
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
            
            # The wakeword service will return a prediction dictionary when it has a complete utterance
            prediction, utterance_buffer = kwd_service.process_audio(audio_chunk)

            # --- CORRECTED WAKE WORD LOGIC ---
            if prediction:
                # Find the wake word with the highest score
                top_wakeword = max(prediction, key=prediction.get)
                top_score = prediction[top_wakeword]

                # ONLY proceed if the score is above the threshold
                if top_score >= WAKEWORD_THRESHOLD:
                    log.info(f"--- Actionable wake word detected: {top_wakeword} (Score: {top_score:.2f}) ---")
                    
                    stream.stop_stream()

                    # --- INTERACTION BLOCK ---
                    print(f'\n🎙️  Wake word "{top_wakeword.replace("_v0.1.onnx", "")}" detected, listening for command...')
                    transcription = stt_service.listen_and_transcribe(timeout_ms=3000)
                    
                    if transcription:
                        print(f'🗣️  Transcription: "{transcription}"')
                        llm_response = llm_service.get_response(transcription)
                        print(f"🤖 LLM Response: {llm_response}")
                        tts_service.speak(llm_response)
                        
                        # Follow-up loop
                        while True:
                            print("\nListening for follow-up...")
                            follow_up = stt_service.listen_and_transcribe(timeout_ms=4000)
                            
                            if follow_up:
                                print(f'🗣️  Transcription: "{follow_up}"')
                                llm_response = llm_service.get_response(follow_up)
                                print(f"🤖 LLM Response: {llm_response}")
                                tts_service.speak(llm_response)
                            else:
                                print("\nDialog ended due to inactivity.")
                                break
                    else:
                        log.info("STT service returned no transcription.")
                        print("No transcription was returned.")
                    # --- END OF INTERACTION BLOCK ---

                    # Now, restart the stream and enter cooldown
                    stream.start_stream() 
                    kwd_service.enter_cooldown()
                    print("\n--- Waiting for wake word ---")
            # --- END OF CORRECTED LOGIC ---

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
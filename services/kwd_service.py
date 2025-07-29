import numpy as np
import logging
from collections import deque
from enum import Enum

class KWDService:
    # --- State Machine ---
    class State(Enum):
        WAITING_FOR_SPEECH = 1
        RECORDING_SPEECH = 2
        COOLDOWN = 3

    # --- Configuration ---
    VAD_FRAME_MS = 30
    RATE = 16000
    MAX_INT16 = 32767.0
    PRE_ROLL_BUFFER_DURATION = 0.4
    POST_ROLL_BUFFER_DURATION = 0.5
    OWW_CHUNK_SAMPLES = 1280

    def __init__(self, oww_model, vad, dynamic_rms):
        self.log = logging.getLogger("KWD")
        self.oww_model = oww_model
        self.vad = vad
        self.dynamic_rms = dynamic_rms

        # Initialize buffers and state
        pre_roll_frames = int((self.PRE_ROLL_BUFFER_DURATION * 1000) / self.VAD_FRAME_MS)
        self.pre_roll_buffer = deque(maxlen=pre_roll_frames)
        
        post_roll_frames = int((self.POST_ROLL_BUFFER_DURATION * 1000) / self.VAD_FRAME_MS)
        self.silence_history = deque(maxlen=post_roll_frames)

        self.utterance_buffer = np.array([], dtype=np.int16)
        self.current_state = self.State.WAITING_FOR_SPEECH

    def process_audio(self, audio_chunk_bytes):
        """
        Processes a single chunk of audio, updates the state machine,
        and returns a detection result if a complete utterance is processed.
        """
        chunk_np = np.frombuffer(audio_chunk_bytes, dtype=np.int16)
        
        normalized_chunk = chunk_np.astype(np.float32) / self.MAX_INT16
        rms = np.sqrt(np.mean(normalized_chunk**2))
        threshold = self.dynamic_rms.get_threshold()
        is_speech = self.vad.is_speech(audio_chunk_bytes, sample_rate=self.RATE) and (rms > threshold)

        # State: WAITING_FOR_SPEECH
        if self.current_state == self.State.WAITING_FOR_SPEECH:
            print(f"🎤 Waiting for speech... | RMS: {rms:.3f} | Threshold: {threshold:.3f}", end='\r')
            self.pre_roll_buffer.append(chunk_np)
            
            if is_speech:
                self.dynamic_rms.lock()
                self.log.info(f"Speech detected (RMS: {rms:.3f}). Starting to record utterance.")
                self.utterance_buffer = np.concatenate(list(self.pre_roll_buffer))
                self.utterance_buffer = np.concatenate((self.utterance_buffer, chunk_np))
                self.silence_history.clear()
                self.current_state = self.State.RECORDING_SPEECH
        
        # State: RECORDING_SPEECH
        elif self.current_state == self.State.RECORDING_SPEECH:
            print(f"🔴 Recording utterance...  | RMS: {rms:.3f} | Threshold: {threshold:.3f}", end='\r')
            self.utterance_buffer = np.concatenate((self.utterance_buffer, chunk_np))
            self.silence_history.append(not is_speech)

            if len(self.silence_history) == self.silence_history.maxlen and all(self.silence_history):
                print(" " * 50, end='\r')
                self.log.info(f"Speech ended. Utterance length: {len(self.utterance_buffer)/self.RATE:.2f}s.")
                
                prediction = None
                if len(self.utterance_buffer) >= self.OWW_CHUNK_SAMPLES:
                    self.log.info("--> Sending complete utterance to wake word detector...")
                    prediction = self.oww_model.predict(self.utterance_buffer)
                    formatted_scores = {k.split('/')[-1]: f"{v:.2f}" for k, v in prediction.items()}
                    self.log.info(f"<-- Prediction results: {formatted_scores}")
                else:
                    self.log.warning("Utterance too short to process, discarding.")

                # Reset state and buffer AFTER processing is complete
                self.current_state = self.State.WAITING_FOR_SPEECH
                self.utterance_buffer = np.array([], dtype=np.int16)

                self.dynamic_rms.reset()

                if prediction:
                    return prediction, self.utterance_buffer

        # State: COOLDOWN
        elif self.current_state == self.State.COOLDOWN:
            print("🤫 Cooldown active...", end='\r')
            self.silence_history.append(not is_speech)
            if len(self.silence_history) == self.silence_history.maxlen and all(self.silence_history):
                self.log.info("--- Cooldown finished. KWD is on. ---")
                print(f"\n▶️  --- KWD is on ---")
                self.current_state = self.State.WAITING_FOR_SPEECH

        return None, None

    def enter_cooldown(self):
        """Forces the service into the cooldown state."""
        self.log.info(f"--- Cooldown started ---")
        self.silence_history.clear()
        self.current_state = self.State.COOLDOWN
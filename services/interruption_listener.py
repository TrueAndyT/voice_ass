import sounddevice as sd
import threading

class InterruptionListener(threading.Thread):
    def __init__(self, wakeword_service, tts_service, active_event, dialog_mode_flag):
        super().__init__(daemon=True)
        self.ww = wakeword_service
        self.tts = tts_service
        self.chunk_duration = 0.5  # seconds
        self.running = True
        self.active = active_event       # True when interruption is allowed
        self.in_dialog_mode = dialog_mode_flag  # True during dialog mode

    def run(self):
        print("🔎 Interruption listener running...")
        while self.running:
            if not self.active.is_set():
                continue

            try:
                audio_chunk = sd.rec(int(self.ww.RATE * self.chunk_duration), samplerate=self.ww.RATE, channels=1, dtype='int16')
                sd.wait()
                mono_chunk = audio_chunk[:, 0].tobytes()
                prediction, _ = self.ww.process_audio(mono_chunk)

                if prediction:
                    for k, v in prediction.items():
                        if k.lower() == "alexa" and v > 0.5:
                            print(f"🛑 Interrupt detected: {k} ({v:.2f})")
                            self.tts.interrupt()
                            if self.in_dialog_mode.is_set():
                                print("🔁 Exiting dialog mode due to interruption.")
                                self.in_dialog_mode.clear()

            except Exception as e:
                print(f"[Interruption Listener Error] {e}")

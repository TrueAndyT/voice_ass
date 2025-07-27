# 🎙️ Miss Heart – Local Voice Assistant

Miss Heart is a fully local, modular voice assistant designed to run offline on Windows/Linux using your laptop’s microphone and speakers. It leverages **OpenWakeWord**, **Whisper**, **Mistral via Ollama**, and **Kokoro TTS** to enable private, real-time voice interaction.

---

## 🧠 Features

- **Wake Word Detection** (Hey Jarvis / Hey Mycroft) via OpenWakeWord
- **Voice Activity Detection** with webrtcvad + RMS filtering
- **Speech-to-Text (STT)** using OpenAI Whisper with GPU acceleration
- **LLM Response Generation** with Mistral 7B via Ollama
- **Text-to-Speech (TTS)** using Kokoro with custom voice `af_heart`
- **Follow-up Dialog Mode** with silence timeout
- **Full GPU Utilization** if available (CUDA)
- **Extensive Logging** (wake word, STT output, LLM dialog)
- **No cloud API calls** – everything runs locally

---

## 🗂️ Project Structure

```

.
├── main.py                 # Orchestrates the whole assistant loop
├── services/
│   ├── loader.py           # Loads and warms up all services
│   ├── wakeword.py         # Wake word detection service
│   ├── stt\_service.py      # Whisper-based speech-to-text
│   ├── tts\_service.py      # Kokoro-based text-to-speech
│   ├── llm\_service.py      # Mistral LLM via Ollama
│   └── logger.py           # File-based logging setup
├── models/                 # Wake word .onnx model files
├── logs/                   # Wake word and runtime logs
├── stt/                    # Transcriptions saved here
├── llm/                    # LLM dialog logs

````

---

## 🚀 Getting Started

1. **Install Python 3.10+ and venv**
2. **Set up environment**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

3. **Dependencies**
    - `torch`, `numpy`, `sounddevice`, `webrtcvad`, `pyaudio`, `openwakeword`, `whisper`, `ollama`, `kokoro`

4. **Start Ollama**
    ```bash
    ollama run mistral
    ```

5. **Place ONNX wake word models**
    ```
    models/hey_jarvis_v0.1.onnx
    models/hey_mycroft_v0.1.onnx
    ```

6. **Launch the assistant**
    ```bash
    python main.py
    ```

---

## 🔐 Offline by Design

This assistant does **not** use cloud APIs. Your voice never leaves your machine.

---

## 🛠️ Configuration

Adjust thresholds, timeouts, device preferences, and model settings directly in:

- `main.py` – for rate, thresholds
- `stt_service.py` – VAD config, language filtering
- `llm_service.py` – system prompt and behavior
- `tts_service.py` – Kokoro voice model, rate

---

## 📓 Logs

- Wake word and system logs: `logs/wakeword.log`
- Transcriptions: `stt/stt_out_<timestamp>.log`
- LLM dialog: `llm/dialog_<timestamp>.log`

---

## 🧪 Tips

- Speak clearly and naturally when triggering wake words.
- If transcription quality drops, verify your mic input level and Whisper model size.
- Set `RMS_THRESHOLD` and `no_speech_threshold` carefully to avoid false triggers or early cutoffs.

---

## 🧤 Credits

- [OpenWakeWord](https://github.com/dscripka/openWakeWord)
- [Whisper](https://github.com/openai/whisper)
- [Ollama](https://github.com/jmorganca/ollama)
- [Kokoro TTS](https://github.com/remsky/Kokoro-FastAPI)

---

## ❤️ Voice Persona

Miss Heart is designed to be brief, caring, and warm, speaking in a feminine voice via Kokoro's `af_heart` model. She avoids filler words and emoji to ensure clarity when voiced.

---

## 📌 TODO

- Add interruption detection (stop TTS if user speaks)
- Timeout-based exit from dialog mode
- Background launcher service
- GUI frontend (optional)

---
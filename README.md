# 🎙️ Alexa (Miss Heart) — Fully‑Local Voice Assistant

Alexa is a **fully local**, modular voice assistant that runs on Linux/Windows with your laptop microphone and speakers. It uses **OpenWakeWord**, **Whisper**, **Llama 3.1 via Ollama**, **Kokoro TTS**, and optional **local RAG** (LlamaIndex + FAISS) for private, real‑time voice interaction — no cloud calls by default.

---

## 🧠 Highlights

- **Wake Word** via OpenWakeWord (ONNX) — low‑latency, 16 kHz pipeline
- **VAD + Dynamic RMS** noise gating to reduce false triggers
- **STT** with OpenAI Whisper (`small.en`, GPU‑accelerated if available)
- **LLM** with **Ollama** (default: `llama3.1:8b-instruct-q4_K_M`; alias `alexa-4k`)
- **TTS** with **Kokoro (hexgrad/Kokoro‑82M)** — fast, warm voice `af_heart`
- **Streaming LLM→TTS**: speak partial responses immediately (SSE)
- **Local file search (RAG)** via LlamaIndex + FAISS, opt‑in
- **Structured logging** for app & perf, rotating STT transcripts
- **No cloud APIs** needed for voice loop; optional web search integration

---

## 🗂️ Project Layout

```

.
├── main.py                     # Application loop (wake word → STT → LLM → TTS)
├── services/
│   ├── microservices\_loader.py # Starts FastAPI microservices (TTS/STT/LLM)
│   ├── service\_manager.py      # Spawns & tracks uvicorn processes
│   ├── llm\_streaming\_server.py # LLM SSE server (/chat, /chat/stream)
│   ├── stt\_service\_server.py   # STT server (/transcribe)
│   ├── tts\_service\_server.py   # TTS server (/speak)
│   ├── stt\_client.py           # HTTP client for STT microservice
│   ├── llm\_streaming\_client.py # HTTP/SSE client + StreamingTTSIntegration
│   ├── tts\_client.py           # HTTP client for TTS microservice
│   ├── kwd\_service.py          # Wake-word detection w/ VAD + RMS checks
│   ├── dynamic\_rms\_service.py  # Adaptive noise thresholding
│   ├── llm\_service.py          # LLM flow, intents, handlers, dialog logging
│   ├── llama\_indexing\_service.py / llama\_file\_search\_service.py # RAG
│   ├── handlers/               # file\_search, memory, note, web\_search
│   └── logger.py               # JSON logs + colored console
├── config/
│   ├── Modelfile               # ollama model alias (alexa-4k)
│   ├── system\_prompt.txt       # persona + style
│   ├── llm\_responses.json      # canned strings for handlers
│   ├── search\_config.json      # RAG input folders
│   ├── notes.json, memory.log  # local notes & memory
│   └── sounds/kwd\_success.wav  # wake chime
├── models/
│   └── alexa\_v0.1.onnx         # OpenWakeWord model (required)
└── docs/
└── LOGGING.md, services.md, …

````

---

## 🚀 Quick Start (Linux Mint)

1) **System deps**

```bash
sudo apt-get update
sudo apt-get install -y python3-venv python3-dev portaudio19-dev ffmpeg jq
````

2. **Create env**

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip wheel
pip install -r requirements.txt
```

3. **Ollama + model**

* Install Ollama: [https://ollama.com/download](https://ollama.com/download)
* Pull base model and build alias:

```bash
ollama pull llama3.1:8b-instruct-q4_K_M
# Optional: create local alias from config/Modelfile
ollama create alexa-4k -f config/Modelfile
```

4. **Models & audio**

* Place **wake word** model at: `models/alexa_v0.1.onnx`
* Ensure the **wake chime** exists: `config/sounds/kwd_success.wav`

5. **Optional web search**

Create a `.env` in the repo root:

```bash
# NOTE: Variable name matches current code (typo kept for compatibility)
TRAVILY_API=sk_...   # Tavily Search API key
```

> ⚠️ Heads‑up: the code expects `TRAVILY_API` (with an “R”). If you prefer `TAVILY_API`, update `services/web_search_service.py` accordingly.

6. **Start (microservices mode, recommended)**

```bash
python3 main.py
```

This will:

* Spawn **TTS** on `:8001`, **STT** on `:8002`, **LLM (SSE)** on `:8003`
* Load OpenWakeWord + VAD locally
* Announce readiness and listen for the wake word

Health endpoints:

* `http://127.0.0.1:8001/health` (TTS), `:8002/health` (STT), `:8003/health` (LLM)

7. **Build local RAG index (optional)**

Edit `config/search_config.json` to list folders to index, then:

```bash
python3 main.py --index
```

This creates a FAISS index in `config/faiss_index/`. You can then ask, e.g., “find the project map” or “search docs about logging”.

---

## 🗣️ How It Works (loop)

1. **Wake** — KWD buffers 1s windows, filters with dynamic RMS + VAD, and detects the wake word.
2. **STT** — 16 kHz mono chunks are recorded until silence; Whisper `small.en` transcribes.
3. **LLM** — Prompt goes to Ollama (default `alexa-4k`/llama 3.1). If a handler intent is detected (notes, memory, web/file search), it routes accordingly.
4. **Streaming TTS** — The LLM SSE stream is chunked and immediately spoken by Kokoro (`af_heart`); any residual text is flushed at completion. Fallback to non‑streaming if SSE fails.

---

## ⚙️ Configuration

* **Persona**: `config/system_prompt.txt`
* **Canned strings**: `config/llm_responses.json`
* **Notes & memory**: `config/notes.json`, `config/memory.log`
* **RAG**: `config/search_config.json`, persisted index `config/faiss_index/`
* **Wake chime**: `config/sounds/kwd_success.wav`

---

## 🧾 Logs

See `docs/LOGGING.md` for full details. Key files:

* `logs/app.jsonl` — structured app logs (all services)
* `logs/performance.jsonl` — durations, token/s, etc.
* `logs/dialog_YYYY-MM-DD_HH-MM-SS.log` — per‑session conversations
* `logs/transcriptions.log` (+ daily rotation) — raw STT text

Handy:

```bash
tail -f logs/app.jsonl | jq .
tail -f logs/performance.jsonl | jq .
```

---

## 🔌 Troubleshooting

* **No mic / ALSA warnings**: ensure `portaudio19-dev` installed; PulseAudio/JACK noise is suppressed in microservices servers.
* **Wake word not triggering**: confirm `models/alexa_v0.1.onnx` exists; reduce background noise or tweak the dynamic RMS multiplier.
* **No TTS audio**: verify default audio sink; `sd.OutputStream` uses system default.
* **SSE stalls**: check firewall (ports 8001–8003), and that `ollama serve` is reachable.
* **Web search empty**: verify `.env` key; confirm the env var name (`TRAVILY_API`) matches the code or update the code.

---

## 📦 Requirements

* Python 3.10+
* `pyaudio`, `webrtcvad` or OpenWakeWord VAD, `numpy`
* `torch`, `openai-whisper`
* `ollama` (daemon running)
* `kokoro` (hexgrad/Kokoro-82M via `KPipeline`)
* `fastapi`, `uvicorn`, `sseclient-py`
* `llama-index`, `faiss-cpu`, `sentence-transformers`
* `requests`, `rich`, `psutil`
* (Optional) `.env` with Tavily API key

Install via:

```bash
pip install -r requirements.txt
```

---

## 🛣️ Roadmap

* Barge‑in (interrupt TTS on user speech)
* Tunable KWD thresholds & per‑environment calibration
* WebSocket/GRPC for lower‑latency streaming
* Unified config file for ports/devices/models
* Cross‑platform audio device selection UI

---

## ❤️ Voice Persona

Alexa speaks in a concise, warm female voice (`af_heart`), avoids filler, and keeps responses short for voice UX.

```

---
import torch
import webrtcvad
import numpy as np
import os
from openwakeword.model import Model
from .stt_service import STTService
from .llm_service import LLMService
from .tts_service import TTSService

def load_services():
    print("Loading services...")
    
    vad = webrtcvad.Vad(1)

    model_paths = [
        os.path.join("models", "alexa_v0.1.onnx")
    ]

    oww_model = Model(wakeword_model_paths=model_paths)

    stt_service = STTService()
    llm_service = LLMService(model='llama3.1:8b-instruct-q4_K_M')
    tts_service = TTSService()

    print("Warming up models (this may take a moment)...")

    # Warm up OpenWakeWord
    oww_chunk_samples = 1280
    silent_oww_chunk = np.zeros(oww_chunk_samples, dtype=np.int16)
    oww_model.predict(silent_oww_chunk)

    # Warm up Whisper STT
    if stt_service.device == 'cuda':
        rate = 16000
        silent_whisper_chunk = np.zeros(rate, dtype=np.float32)
        stt_service.model.transcribe(silent_whisper_chunk, fp16=True)

    # Warm up Kokoro TTS
    tts_service.warmup()

    # Warm up LLM without polluting conversation
    llm_service.warmup_llm()

    print("✅ Models are loaded and ready.")
    
    return vad, oww_model, stt_service, llm_service, tts_service

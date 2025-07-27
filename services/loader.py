import torch
import webrtcvad
import numpy as np
import os
import subprocess
import atexit
import time
import requests
from openwakeword.model import Model
from .stt_service import STTService
from .llm_service import LLMService


def load_services():
    """Loads and warms up all AI models."""
    print("Loading services...")
    
    vad = webrtcvad.Vad(1)

    model_paths = [
        os.path.join("models", "hey_jarvis_v0.1.onnx"),
        os.path.join("models", "hey_mycroft_v0.1.onnx")
    ]

    oww_model = Model(wakeword_model_paths=model_paths)

    stt_service = STTService()
    llm_service = LLMService()

    print("Warming up models (this may take a moment)...")

    oww_chunk_samples = 1280
    silent_oww_chunk = np.zeros(oww_chunk_samples, dtype=np.int16)
    oww_model.predict(silent_oww_chunk)

    if stt_service.device == 'cuda':
        rate = 16000
        silent_whisper_chunk = np.zeros(rate, dtype=np.float32)
        stt_service.model.transcribe(silent_whisper_chunk, fp16=True)

    llm_service.get_response("Respond with only the word 'ready'")

    print("✅ Models are loaded and ready.")
    
    return vad, oww_model, stt_service, llm_service

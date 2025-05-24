import torch
from faster_whisper import WhisperModel
from TTS.api import TTS
from transformers import AutoTokenizer, AutoModelForCausalLM
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from torch.serialization import add_safe_globals
from TTS.tts.configs.xtts_config import XttsConfig, XttsAudioConfig
from TTS.tts.models.xtts import XttsArgs
from TTS.config.shared_configs import BaseDatasetConfig

# Добавляем безопасные глобальные переменные для XTTS
add_safe_globals([XttsConfig, XttsAudioConfig, BaseDatasetConfig, XttsArgs])

# Глобальные переменные для хранения загруженных моделей
whisper_model = None
tts_model = None
xtts_model = None

def get_whisper_model():
    global whisper_model
    if whisper_model is None:
        print("Loading Whisper model (first time)...")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        compute_type = "float16" if device == "cuda" else "int8"
        print(f"Using device: {device}, compute type: {compute_type}")
        
        try:
            whisper_model = WhisperModel("large-v3", 
                                       device=device, 
                                       compute_type=compute_type,
                                       num_workers=2, 
                                       cpu_threads=4)
            # Проверяем доступность памяти GPU
            if device == "cuda":
                torch.cuda.empty_cache()
                print(f"Available GPU memory: {torch.cuda.memory_allocated() / 1024**2:.2f} MB")
        except Exception as e:
            print(f"Error loading Whisper model: {str(e)}")
            raise
    return whisper_model

def get_tts_model():
    global tts_model
    if tts_model is None:
        print("Loading Coqui TTS model (first time)...")
        tts_model = TTS("tts_models/en/vctk/vits")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        tts_model.to(device)  # Современный синтаксис вместо gpu=True
    return tts_model

def get_xtts_model():
    global xtts_model
    if xtts_model is None:
        print("Loading XTTS model (first time)...")
        xtts_model = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        xtts_model.to(device)
    return xtts_model
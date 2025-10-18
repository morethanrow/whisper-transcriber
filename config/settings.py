import os
from typing import Set

class Config:
    """Конфигурация приложения"""
    
    # Настройки Whisper
    WHISPER_MODEL = os.getenv("WHISPER_MODEL", "medium")  # Используем medium вместо small для лучшего качества
    COMPUTE_TYPE = os.getenv("COMPUTE_TYPE", "int8")
    
    # Настройки сервера
    PORT = int(os.getenv("PORT", 8000))
    HOST = os.getenv("HOST", "0.0.0.0")
    
    # Поддерживаемые форматы аудио
    SUPPORTED_AUDIO_FORMATS: Set[str] = {'.mp3', '.wav', '.m4a', '.mp4', '.flac', '.ogg'}
    
    # Настройки для ffmpeg - оптимизированы для Whisper
    FFMPEG_SAMPLE_RATE = 16000  # Whisper работает лучше с 16kHz
    FFMPEG_CHANNELS = 1  # Моно для лучшего качества распознавания
    
    # Настройки транскрипции
    DEFAULT_LANGUAGE = "ru"
    DEFAULT_SEGMENT_DURATION = 600  # секунды
    
    # Настройки Whisper для транскрипции
    WHISPER_BEAM_SIZE = 5
    WHISPER_BEST_OF = 5
    WHISPER_TEMPERATURES = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    WHISPER_VAD_FILTER = False  # Отключаем VAD фильтр, чтобы не пропускать начало
    WHISPER_WORD_TIMESTAMPS = True
    WHISPER_CONDITION_ON_PREVIOUS_TEXT = True
    
    # Промпты для разных языков
    LANGUAGE_PROMPTS = {
        "ru": "Это диалог на русском языке.",
        "en": "This is a dialogue in English.",
        "es": "Este es un diálogo en español.",
        "fr": "Ceci est un dialogue en français.",
        "de": "Dies ist ein Dialog auf Deutsch.",
        "it": "Questo è un dialogo in italiano.",
        "pt": "Este é um diálogo em português.",
        "ja": "これは日本語の対話です。",
        "ko": "이것은 한국어 대화입니다.",
        "zh": "这是中文对话。"
    }

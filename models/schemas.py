from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class TranscriptionSegment:
    """Сегмент транскрипции"""
    start: float
    end: float
    text: str

@dataclass
class TranscriptionResult:
    """Результат транскрипции"""
    success: bool
    text: str
    language: str
    language_probability: float
    duration: float
    segments: List[TranscriptionSegment]
    error: Optional[str] = None

@dataclass
class AudioSegment:
    """Сегмент аудио"""
    segment: int
    start_time: float
    end_time: float
    duration: float
    audio_data: str  # base64 encoded

@dataclass
class SplitResult:
    """Результат разделения аудио"""
    success: bool
    total_duration: float
    segment_duration: int
    num_segments: int
    segments: List[AudioSegment]
    error: Optional[str] = None

@dataclass
class HealthStatus:
    """Статус здоровья API"""
    ok: bool
    model: str
    compute_type: str
    whisper_loaded: bool
    supported_formats: List[str]

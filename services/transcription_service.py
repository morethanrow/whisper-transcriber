import os
import tempfile
from typing import Dict, Any
from faster_whisper import WhisperModel
from config.settings import Config
from services.audio_processor import AudioProcessor
from models.schemas import TranscriptionSegment, TranscriptionResult

class TranscriptionService:
    """Сервис транскрипции"""
    
    def __init__(self):
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Загружает модель Whisper"""
        try:
            print(f"Loading Whisper model: {Config.WHISPER_MODEL} with compute type: {Config.COMPUTE_TYPE}")
            self.model = WhisperModel(Config.WHISPER_MODEL, compute_type=Config.COMPUTE_TYPE)
            print("Whisper model loaded successfully!")
        except Exception as e:
            print(f"Error loading Whisper model: {e}")
            self.model = None
    
    def transcribe(self, audio_path: str, language: str = None) -> TranscriptionResult:
        """
        Транскрибирует аудиофайл
        
        Args:
            audio_path: путь к аудиофайлу
            language: язык для транскрипции
            
        Returns:
            TranscriptionResult с результатами транскрипции
        """
        if language is None:
            language = Config.DEFAULT_LANGUAGE
            
        if self.model is None:
            return TranscriptionResult(
                success=False,
                text="",
                language=language,
                language_probability=0.0,
                duration=0.0,
                segments=[],
                error="Whisper model not loaded"
            )
        
        try:
            # Сначала конвертируем аудио в оптимальный формат для Whisper
            temp_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            temp_wav.close()
            
            # Конвертируем в WAV с оптимальными параметрами для Whisper
            if not AudioProcessor.convert_to_wav(audio_path, temp_wav.name):
                return TranscriptionResult(
                    success=False,
                    text="",
                    language=language,
                    language_probability=0.0,
                    duration=0.0,
                    segments=[],
                    error="Failed to convert audio to WAV format"
                )
            
            # Получаем промпт для языка
            initial_prompt = Config.LANGUAGE_PROMPTS.get(language)
            
            # Выполняем транскрипцию с улучшенными параметрами
            segments, info = self.model.transcribe(
                temp_wav.name,
                language=language,
                beam_size=Config.WHISPER_BEAM_SIZE,
                best_of=Config.WHISPER_BEST_OF,
                temperature=Config.WHISPER_TEMPERATURES,
                vad_filter=Config.WHISPER_VAD_FILTER,
                word_timestamps=Config.WHISPER_WORD_TIMESTAMPS,
                condition_on_previous_text=Config.WHISPER_CONDITION_ON_PREVIOUS_TEXT,
                initial_prompt=initial_prompt
            )
            
            # Собираем результаты
            transcription_segments = []
            full_text = ""
            
            for segment in segments:
                segment_data = TranscriptionSegment(
                    start=segment.start,
                    end=segment.end,
                    text=segment.text.strip()
                )
                transcription_segments.append(segment_data)
                full_text += segment.text.strip() + " "
            
            # Очищаем временный файл
            try:
                os.unlink(temp_wav.name)
            except:
                pass
            
            return TranscriptionResult(
                success=True,
                text=full_text.strip(),
                language=info.language,
                language_probability=info.language_probability,
                duration=info.duration,
                segments=transcription_segments
            )
            
        except Exception as e:
            # Очищаем временный файл в случае ошибки
            try:
                if 'temp_wav' in locals():
                    os.unlink(temp_wav.name)
            except:
                pass
            
            return TranscriptionResult(
                success=False,
                text="",
                language=language,
                language_probability=0.0,
                duration=0.0,
                segments=[],
                error=str(e)
            )

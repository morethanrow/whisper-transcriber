"""
Сервис для работы с аудио файлами
"""
import os
import json
import subprocess
import tempfile
from typing import List, Dict, Any, Optional
from faster_whisper import WhisperModel

from src.models.transcription import TranscriptionResult
from src.utils.file_parser import format_text_to_paragraphs


class AudioService:
    """Сервис для обработки аудио файлов"""
    
    def __init__(self, model: WhisperModel):
        self.model = model
    
    def get_audio_duration(self, file_path: str) -> float:
        """Получает длительность аудио файла в секундах"""
        try:
            duration_cmd = [
                "ffprobe", "-v", "quiet", "-print_format", "json", 
                "-show_format", file_path
            ]
            
            result = subprocess.run(duration_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                return 0.0
            
            duration_data = json.loads(result.stdout)
            return float(duration_data["format"]["duration"])
        except Exception:
            return 0.0
    
    def split_audio_file(self, input_path: str, segment_duration: int = 600) -> List[str]:
        """
        Разделяет аудио файл на сегменты заданной длительности
        
        Args:
            input_path: Путь к входному файлу
            segment_duration: Длительность сегмента в секундах (по умолчанию 600 = 10 минут)
        
        Returns:
            Список путей к созданным сегментам
        """
        duration = self.get_audio_duration(input_path)
        if duration <= segment_duration:
            return [input_path]
        
        segments = []
        num_segments = int(duration / segment_duration) + (1 if duration % segment_duration > 0 else 0)
        
        for i in range(num_segments):
            start_time = i * segment_duration
            end_time = min((i + 1) * segment_duration, duration)
            
            # Создаем временный файл для сегмента
            segment_path = tempfile.mktemp(suffix=f"_segment_{i+1}.mp3")
            
            # Используем ffmpeg для нарезки
            split_cmd = [
                "ffmpeg", "-i", input_path,
                "-ss", str(start_time),
                "-t", str(end_time - start_time),
                "-c:a", "libmp3lame",  # Перекодируем в MP3
                "-b:a", "128k",  # Битрейт 128kbps
                "-y",  # Перезаписывать файл без подтверждения
                segment_path
            ]
            
            result = subprocess.run(split_cmd, capture_output=True, text=True)
            if result.returncode == 0:
                segments.append(segment_path)
            else:
                print(f"Failed to create segment {i+1}: {result.stderr}")
                # Удаляем частично созданный файл
                if os.path.exists(segment_path):
                    os.unlink(segment_path)
                raise Exception(f"FFmpeg failed to create segment {i+1}: {result.stderr}")
        
        if not segments:
            raise Exception("Failed to create any audio segments")
        
        return segments
    
    def transcribe_segment(self, segment_path: str, language: str = "ru") -> Dict[str, Any]:
        """Транскрибирует один сегмент аудио"""
        try:
            segments, info = self.model.transcribe(
                segment_path,
                language=language if language != "auto" else None,
                beam_size=5
            )
            
            # Собираем результат
            transcription_text = ""
            segments_list = []
            
            for segment in segments:
                segment_data = {
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip()
                }
                segments_list.append(segment_data)
                transcription_text += segment.text.strip() + " "
            
            return {
                "text": transcription_text.strip(),
                "segments": segments_list,
                "language": info.language,
                "language_probability": info.language_probability,
                "duration": info.duration
            }
        except Exception as e:
            raise Exception(f"Transcription failed for segment: {str(e)}")
    
    def transcribe_audio(
        self, 
        file_path: str, 
        filename: str, 
        language: str = "ru",
        recorded_at: Optional[str] = None,
        model_name: str = "whisper-small:int8"
    ) -> TranscriptionResult:
        """
        Транскрибирует аудио файл
        
        Args:
            file_path: Путь к аудио файлу
            filename: Имя файла
            language: Язык для распознавания
            recorded_at: Дата/время записи
            model_name: Название модели
        
        Returns:
            Результат транскрибации
        """
        try:
            # Получаем длительность аудио
            duration = self.get_audio_duration(file_path)
            
            # Разделяем файл на сегменты если он больше 10 минут
            segment_paths = self.split_audio_file(file_path, segment_duration=600)
            
            # Транскрибируем каждый сегмент
            all_text = ""
            all_segments = []
            total_duration = 0
            detected_language = language
            language_probability = 1.0
            
            for i, segment_path in enumerate(segment_paths):
                try:
                    # Проверяем, что сегмент был создан успешно
                    if not os.path.exists(segment_path):
                        raise Exception(f"Segment file {segment_path} was not created")
                    
                    segment_result = self.transcribe_segment(segment_path, language)
                    
                    # Объединяем результаты
                    all_text += segment_result["text"] + " "
                    all_segments.extend(segment_result["segments"])
                    total_duration += segment_result["duration"]
                    
                    # Используем язык и вероятность из первого сегмента
                    if i == 0:
                        detected_language = segment_result["language"]
                        language_probability = segment_result["language_probability"]
                    
                except Exception as e:
                    print(f"Failed to transcribe segment {i+1}: {str(e)}")
                    raise Exception(f"Failed to transcribe segment {i+1}: {str(e)}")
                finally:
                    # Удаляем временный файл сегмента (если это не исходный файл)
                    if segment_path != file_path and os.path.exists(segment_path):
                        os.unlink(segment_path)
            
            # Разделяем текст на параграфы
            paragraphs = format_text_to_paragraphs(all_text.strip())
            
            return TranscriptionResult(
                filename=filename,
                recorded_at=recorded_at,
                duration_sec=total_duration,
                model=model_name,
                status="ok",
                language=detected_language,
                text=all_text.strip(),
                paragraphs=paragraphs
            )
            
        except Exception as e:
            return TranscriptionResult(
                filename=filename,
                recorded_at=recorded_at,
                duration_sec=0,
                model=model_name,
                status="error",
                error_code="TRANSCRIPTION_FAILED",
                error_message=str(e)
            )

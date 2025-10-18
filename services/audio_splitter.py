import os
import base64
import tempfile
import subprocess
from typing import Dict, Any
from config.settings import Config
from services.audio_processor import AudioProcessor
from models.schemas import AudioSegment, SplitResult

class AudioSplitter:
    """Разделение аудиофайлов на части"""
    
    @staticmethod
    def split_audio(input_path: str, segment_duration: int = None) -> SplitResult:
        """
        Разделяет аудиофайл на части
        
        Args:
            input_path: путь к входному файлу
            segment_duration: длительность сегмента в секундах
            
        Returns:
            SplitResult с результатами разделения
        """
        if segment_duration is None:
            segment_duration = Config.DEFAULT_SEGMENT_DURATION
            
        try:
            # Получаем длительность файла
            total_duration = AudioProcessor.get_audio_duration(input_path)
            if total_duration is None:
                return SplitResult(
                    success=False,
                    total_duration=0,
                    segment_duration=segment_duration,
                    num_segments=0,
                    segments=[],
                    error="Could not determine audio duration"
                )
            
            # Вычисляем количество сегментов
            num_segments = int(total_duration / segment_duration) + 1
            
            segments = []
            temp_files = []
            
            for i in range(num_segments):
                start_time = i * segment_duration
                end_time = min((i + 1) * segment_duration, total_duration)
                
                # Создаем временный файл для сегмента
                temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                temp_files.append(temp_file.name)
                temp_file.close()
                
                # Извлекаем сегмент
                ffmpeg_cmd = [
                    "ffmpeg",
                    "-i", input_path,
                    "-ss", str(start_time),
                    "-t", str(end_time - start_time),
                    "-acodec", "pcm_s16le",
                    "-ar", str(Config.FFMPEG_SAMPLE_RATE),
                    "-ac", str(Config.FFMPEG_CHANNELS),
                    "-y",
                    temp_file.name
                ]
                
                result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    # Читаем файл и конвертируем в base64
                    with open(temp_file.name, 'rb') as f:
                        audio_data = f.read()
                        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                    
                    segments.append(AudioSegment(
                        segment=i + 1,
                        start_time=start_time,
                        end_time=end_time,
                        duration=end_time - start_time,
                        audio_data=audio_base64
                    ))
            
            # Очищаем временные файлы
            for temp_file in temp_files:
                try:
                    os.unlink(temp_file)
                except:
                    pass
            
            return SplitResult(
                success=True,
                total_duration=total_duration,
                segment_duration=segment_duration,
                num_segments=len(segments),
                segments=segments
            )
            
        except Exception as e:
            return SplitResult(
                success=False,
                total_duration=0,
                segment_duration=segment_duration,
                num_segments=0,
                segments=[],
                error=str(e)
            )

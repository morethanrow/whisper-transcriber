import os
import subprocess
from typing import Optional
from config.settings import Config

class AudioProcessor:
    """Обработка аудиофайлов"""
    
    @staticmethod
    def is_audio_file(filename: str) -> bool:
        """Проверяет, является ли файл аудио"""
        if not filename:
            return False
        
        # Проверяем расширение
        ext = os.path.splitext(filename.lower())[1]
        return ext in Config.SUPPORTED_AUDIO_FORMATS
    
    @staticmethod
    def convert_to_wav(input_path: str, output_path: str) -> bool:
        """Конвертирует аудиофайл в WAV формат"""
        try:
            ffmpeg_cmd = [
                "ffmpeg",
                "-i", input_path,
                "-acodec", "pcm_s16le",
                "-ar", str(Config.FFMPEG_SAMPLE_RATE),
                "-ac", str(Config.FFMPEG_CHANNELS),
                "-y",  # overwrite output file
                output_path
            ]
            
            result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
            return result.returncode == 0
            
        except Exception as e:
            print(f"Error converting audio: {e}")
            return False
    
    @staticmethod
    def get_audio_duration(file_path: str) -> Optional[float]:
        """Получает длительность аудиофайла"""
        try:
            ffprobe_cmd = [
                "ffprobe",
                "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "csv=p=0",
                file_path
            ]
            
            result = subprocess.run(ffprobe_cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return float(result.stdout.strip())
            return None
            
        except Exception as e:
            print(f"Error getting duration: {e}")
            return None

import os
import tempfile
from typing import Dict, Any
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

# Импорты из наших модулей
from config.settings import Config
from models.schemas import HealthStatus, TranscriptionResult, SplitResult
from services.audio_processor import AudioProcessor
from services.audio_splitter import AudioSplitter
from services.transcription_service import TranscriptionService

# ============================================================================
# FASTAPI ПРИЛОЖЕНИЕ
# ============================================================================

app = FastAPI(
    title="Whisper Transcription API",
    description="Простой и быстрый API для транскрипции аудио с помощью Whisper",
    version="2.0.0"
)

# Инициализация сервисов
transcription_service = TranscriptionService()

@app.get("/health")
async def health_check() -> HealthStatus:
    """Проверка состояния API и модели"""
    return HealthStatus(
        ok=True,
        model=Config.WHISPER_MODEL,
        compute_type=Config.COMPUTE_TYPE,
        whisper_loaded=transcription_service.model is not None,
        supported_formats=list(Config.SUPPORTED_AUDIO_FORMATS)
    )

@app.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str = Config.DEFAULT_LANGUAGE
) -> Dict[str, Any]:
    """
    Транскрибирует аудиофайл
    
    Args:
        file: аудиофайл для транскрипции
        language: язык для транскрипции (по умолчанию 'ru')
    
    Returns:
        JSON с результатами транскрипции
    """
    # Проверяем тип файла
    if not AudioProcessor.is_audio_file(file.filename):
        raise HTTPException(
            status_code=400, 
            detail=f"File must be an audio file. Supported formats: {', '.join(Config.SUPPORTED_AUDIO_FORMATS)}"
        )
    
    # Создаем временный файл
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1])
    
    try:
        # Сохраняем загруженный файл
        content = await file.read()
        temp_file.write(content)
        temp_file.close()
        
        # Выполняем транскрипцию
        result = transcription_service.transcribe(temp_file.name, language)
        
        if not result.success:
            raise HTTPException(status_code=500, detail=f"Transcription failed: {result.error}")
        
        # Конвертируем результат в словарь для JSON ответа
        return {
            "success": result.success,
            "text": result.text,
            "language": result.language,
            "language_probability": result.language_probability,
            "duration": result.duration,
            "segments": [
                {
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text
                }
                for segment in result.segments
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    
    finally:
        # Очищаем временный файл
        try:
            os.unlink(temp_file.name)
        except:
            pass

@app.post("/split")
async def split_audio(
    file: UploadFile = File(...),
    segment_sec: int = Config.DEFAULT_SEGMENT_DURATION
) -> Dict[str, Any]:
    """
    Разделяет аудиофайл на части
    
    Args:
        file: аудиофайл для разделения
        segment_sec: длительность сегмента в секундах (по умолчанию 600)
    
    Returns:
        JSON с результатами разделения
    """
    # Проверяем тип файла
    if not AudioProcessor.is_audio_file(file.filename):
        raise HTTPException(
            status_code=400, 
            detail=f"File must be an audio file. Supported formats: {', '.join(Config.SUPPORTED_AUDIO_FORMATS)}"
        )
    
    # Создаем временный файл
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1])
    
    try:
        # Сохраняем загруженный файл
        content = await file.read()
        temp_file.write(content)
        temp_file.close()
        
        # Выполняем разделение
        result = AudioSplitter.split_audio(temp_file.name, segment_sec)
        
        if not result.success:
            raise HTTPException(status_code=500, detail=f"Audio splitting failed: {result.error}")
        
        # Конвертируем результат в словарь для JSON ответа
        return {
            "success": result.success,
            "total_duration": result.total_duration,
            "segment_duration": result.segment_duration,
            "num_segments": result.num_segments,
            "segments": [
                {
                    "segment": segment.segment,
                    "start_time": segment.start_time,
                    "end_time": segment.end_time,
                    "duration": segment.duration,
                    "audio_data": segment.audio_data
                }
                for segment in result.segments
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    
    finally:
        # Очищаем временный файл
        try:
            os.unlink(temp_file.name)
        except:
            pass

# ============================================================================
# ЗАПУСК ПРИЛОЖЕНИЯ
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(app, host=Config.HOST, port=Config.PORT)
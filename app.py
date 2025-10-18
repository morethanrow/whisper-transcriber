"""
Audio Transcription Service
Главный файл приложения
"""
import os
import uvicorn
from fastapi import FastAPI

from src.api.routes import create_routes
from src.services.audio_service import AudioService
from src.services.test_service import TestService


def create_app() -> FastAPI:
    """Создает и настраивает FastAPI приложение"""
    
    # Настройки из переменных окружения
    whisper_model = os.getenv("WHISPER_MODEL", "small")
    compute_type = os.getenv("COMPUTE_TYPE", "int8")
    test_results_dir = os.path.join(os.getcwd(), "test_result")
    
    # Инициализация модели Whisper
    print(f"Loading Whisper model: {whisper_model} with compute type: {compute_type}")
    from faster_whisper import WhisperModel
    model = WhisperModel(whisper_model, compute_type=compute_type)
    print("Model loaded successfully!")
    
    # Создание сервисов
    audio_service = AudioService(model)
    test_service = TestService(test_results_dir)
    
    # Создание FastAPI приложения
    app = FastAPI(
        title="Audio Transcription Service", 
        version="2.0.0",
        description="Профессиональный сервис для транскрибации аудио файлов с помощью Whisper"
    )
    
    # Подключение маршрутов
    router = create_routes(audio_service, test_service, whisper_model, compute_type)
    app.include_router(router)
    
    return app


# Создание приложения
app = create_app()


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
"""
API маршруты для сервиса транскрибации
"""
import os
import tempfile
from typing import Optional
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from datetime import datetime

from src.models.transcription import TranscriptionResult
from src.services.audio_service import AudioService
from src.services.test_service import TestService
from src.utils.file_parser import parse_datetime_from_filename, validate_audio_file


def create_routes(audio_service: AudioService, test_service: TestService, whisper_model: str, compute_type: str) -> APIRouter:
    """Создает API маршруты"""
    
    router = APIRouter()
    
    @router.get("/health")
    async def health_check():
        """Проверка состояния API и модели"""
        return {
            "ok": True,
            "model": whisper_model,
            "compute_type": compute_type,
            "test_results_dir": test_service.test_results_dir
        }
    
    @router.post("/transcribe")
    async def transcribe_audio(
        file: UploadFile = File(...),
        language: str = Form(default="ru"),
        save_result: bool = Form(default=True)
    ):
        """
        Транскрибация аудиофайла с автоматической нарезкой больших файлов
        
        Args:
            file: Аудиофайл для транскрибации
            language: Язык для распознавания (по умолчанию 'ru')
            save_result: Сохранять ли результат в папку test_result (по умолчанию True)
        
        Returns:
            JSON с распознанным текстом, датой/временем и параграфами
        """
        try:
            # Проверяем тип файла
            if not validate_audio_file(file.filename, file.content_type):
                raise HTTPException(
                    status_code=400, 
                    detail="File must be an audio file. Supported extensions: .mp3, .wav, .m4a, .aac, .flac, .ogg, .wma, .aiff, .au"
                )
            
            # Читаем содержимое файла
            audio_content = await file.read()
            
            # Создаем временный файл для обработки
            input_filename = file.filename or "input_audio"
            input_extension = input_filename.split('.')[-1] if '.' in input_filename else 'mp3'
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{input_extension}") as temp_file:
                temp_file.write(audio_content)
                temp_file_path = temp_file.name
            
            try:
                # Парсим дату/время из имени файла
                recorded_at = parse_datetime_from_filename(input_filename)
                if not recorded_at:
                    # Если не удалось распарсить из имени файла, используем время обработки
                    recorded_at = datetime.now().isoformat()
                
                # Транскрибируем аудио
                model_name = f"whisper-{whisper_model}:{compute_type}"
                result = audio_service.transcribe_audio(
                    temp_file_path,
                    input_filename,
                    language,
                    recorded_at,
                    model_name
                )
                
                # Сохраняем результат если требуется
                saved_file_path = None
                if save_result and result.status == "ok":
                    saved_file_path = test_service.save_test_result(result, input_filename)
                    result_dict = result.to_dict()
                    result_dict["saved_to"] = saved_file_path
                    result_dict["test_number"] = test_service.counter.load_counter() - 1
                    return result_dict
                
                return result.to_dict()
                
            finally:
                # Удаляем временный входной файл
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
            
        except Exception as e:
            # Возвращаем ошибку в новом формате
            error_result = TranscriptionResult(
                filename=file.filename or "unknown",
                recorded_at=None,
                duration_sec=0,
                model=f"whisper-{whisper_model}:{compute_type}",
                status="error",
                error_code="TRANSCRIPTION_FAILED",
                error_message=str(e)
            )
            raise HTTPException(status_code=500, detail=error_result.to_dict())
    
    @router.get("/test-results")
    async def get_test_results():
        """Получает список всех сохраненных результатов тестов"""
        try:
            results = test_service.get_test_results()
            return {"results": results}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get test results: {str(e)}")
    
    @router.get("/test-results/{test_number}")
    async def get_test_result(test_number: int):
        """Получает конкретный результат теста по номеру"""
        try:
            result = test_service.get_test_result(test_number)
            if result is None:
                raise HTTPException(status_code=404, detail=f"Test result {test_number} not found")
            return result
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Failed to get test result: {str(e)}")
    
    return router

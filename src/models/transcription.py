"""
Модели данных для сервиса транскрибации
"""
from typing import List, Optional, Dict, Any
from datetime import datetime


class TranscriptionResult:
    """Результат транскрибации"""
    
    def __init__(
        self,
        filename: str,
        recorded_at: Optional[str],
        duration_sec: float,
        model: str,
        status: str = "ok",
        language: Optional[str] = None,
        text: str = "",
        paragraphs: List[str] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None
    ):
        self.filename = filename
        self.recorded_at = recorded_at
        self.duration_sec = duration_sec
        self.model = model
        self.status = status
        self.language = language
        self.text = text
        self.paragraphs = paragraphs or []
        self.error_code = error_code
        self.error_message = error_message
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразует результат в словарь для JSON ответа"""
        result = {
            "info": {
                "filename": self.filename,
                "recorded_at": self.recorded_at,
                "duration_sec": self.duration_sec,
                "model": self.model
            },
            "result": {
                "status": self.status,
                "language": self.language,
                "text": self.text,
                "paragraphs": self.paragraphs
            }
        }
        
        if self.status == "error":
            result["result"]["error_code"] = self.error_code
            result["result"]["error_message"] = self.error_message
        
        return result


class TestInfo:
    """Информация о тесте"""
    
    def __init__(
        self,
        test_number: int,
        timestamp: str,
        original_filename: str,
        model_used: str,
        compute_type: str
    ):
        self.test_number = test_number
        self.timestamp = timestamp
        self.original_filename = original_filename
        self.model_used = model_used
        self.compute_type = compute_type
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_number": self.test_number,
            "timestamp": self.timestamp,
            "original_filename": self.original_filename,
            "model_used": self.model_used,
            "compute_type": self.compute_type
        }

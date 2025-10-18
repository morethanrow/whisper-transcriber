"""
Сервис для работы с результатами тестов
"""
import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.models.transcription import TranscriptionResult, TestInfo
from src.utils.test_counter import TestCounter


class TestService:
    """Сервис для работы с результатами тестов"""
    
    def __init__(self, test_results_dir: str):
        self.test_results_dir = test_results_dir
        self.counter = TestCounter(test_results_dir)
        os.makedirs(test_results_dir, exist_ok=True)
    
    def save_test_result(self, result: TranscriptionResult, filename: str) -> str:
        """
        Сохраняет результат теста в JSON файл
        
        Args:
            result: Результат транскрипции
            filename: Имя исходного файла
        
        Returns:
            Путь к сохраненному файлу
        """
        test_number = self.counter.get_next_number()
        now = datetime.now()
        timestamp = now.strftime("%d.%m.%Y_%H.%M")
        
        # Создаем имя файла в формате: test_0001_18.10.2025_22.47.json
        result_filename = f"test_{test_number:04d}_{timestamp}.json"
        result_path = os.path.join(self.test_results_dir, result_filename)
        
        # Сохраняем результат в новом формате
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)
        
        return result_path
    
    def get_test_results(self) -> List[Dict[str, Any]]:
        """Получает список всех сохраненных результатов тестов"""
        try:
            if not os.path.exists(self.test_results_dir):
                return []
            
            results = []
            for filename in os.listdir(self.test_results_dir):
                if filename.endswith('.json') and filename.startswith('test_'):
                    file_path = os.path.join(self.test_results_dir, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            # Поддерживаем как старый, так и новый формат
                            if "info" in data and "result" in data:
                                # Новый формат
                                results.append({
                                    "filename": filename,
                                    "test_number": filename.split('_')[1] if '_' in filename else None,
                                    "timestamp": data.get("info", {}).get("recorded_at"),
                                    "original_filename": data.get("info", {}).get("filename"),
                                    "duration": data.get("info", {}).get("duration_sec")
                                })
                            else:
                                # Старый формат (для обратной совместимости)
                                results.append({
                                    "filename": filename,
                                    "test_number": data.get("test_info", {}).get("test_number"),
                                    "timestamp": data.get("test_info", {}).get("timestamp"),
                                    "original_filename": data.get("test_info", {}).get("original_filename"),
                                    "duration": data.get("transcription_result", {}).get("duration")
                                })
                    except Exception as e:
                        print(f"Error reading {filename}: {e}")
            
            # Сортируем по номеру теста
            results.sort(key=lambda x: int(x.get("test_number", 0)) if x.get("test_number") else 0)
            
            return results
        except Exception as e:
            print(f"Failed to get test results: {e}")
            return []
    
    def get_test_result(self, test_number: int) -> Optional[Dict[str, Any]]:
        """Получает конкретный результат теста по номеру"""
        try:
            # Ищем файл с указанным номером теста
            for filename in os.listdir(self.test_results_dir):
                if filename.startswith(f"test_{test_number:04d}_") and filename.endswith('.json'):
                    file_path = os.path.join(self.test_results_dir, filename)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        # Возвращаем данные в том формате, в котором они сохранены
                        return data
            
            return None
        except Exception as e:
            print(f"Failed to get test result: {e}")
            return None

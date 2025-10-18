"""
Управление счетчиком тестов
"""
import os
from typing import Optional


class TestCounter:
    """Класс для управления счетчиком тестов"""
    
    def __init__(self, test_results_dir: str):
        self.test_results_dir = test_results_dir
        self.counter_file = os.path.join(test_results_dir, "test_counter.txt")
    
    def load_counter(self) -> int:
        """Загружает счетчик тестов из файла"""
        try:
            if os.path.exists(self.counter_file):
                with open(self.counter_file, 'r') as f:
                    return int(f.read().strip())
            else:
                return 1
        except (ValueError, FileNotFoundError):
            return 1
    
    def save_counter(self, counter: int) -> None:
        """Сохраняет счетчик тестов в файл"""
        try:
            with open(self.counter_file, 'w') as f:
                f.write(str(counter))
        except Exception as e:
            print(f"Warning: Failed to save test counter: {e}")
    
    def get_next_number(self) -> int:
        """Получает следующий номер теста"""
        counter = self.load_counter()
        self.save_counter(counter + 1)
        return counter

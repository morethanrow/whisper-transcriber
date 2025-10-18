"""
Утилиты для работы с файлами и парсинга
"""
import os
import re
from typing import Optional
from datetime import datetime


def parse_datetime_from_filename(filename: str) -> Optional[str]:
    """
    Парсит дату и время из имени файла
    
    Поддерживаемые шаблоны:
    - YYYY-MM-DD_HH-mm-ss_*.*
    - YYYY-MM-DD_HH.mm.ss_*.*
    - YYYY-MM-DD HH-mm-ss_*.*
    - YYYY-MM-DD HH.mm.ss_*.*
    - YYYY-MM-DD at HH.mm.ss (для формата "Meet 2025-10-18 at 20.01.11")
    
    Args:
        filename: Имя файла
    
    Returns:
        Строка с датой/временем в формате ISO или None
    """
    if not filename:
        return None
    
    # Убираем расширение файла
    name_without_ext = os.path.splitext(filename)[0]
    
    # Паттерны для поиска даты/времени
    patterns = [
        # YYYY-MM-DD_HH-mm-ss
        r'(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2}-\d{2})',
        # YYYY-MM-DD_HH.mm.ss  
        r'(\d{4}-\d{2}-\d{2})_(\d{2}\.\d{2}\.\d{2})',
        # YYYY-MM-DD HH-mm-ss
        r'(\d{4}-\d{2}-\d{2})\s+(\d{2}-\d{2}-\d{2})',
        # YYYY-MM-DD HH.mm.ss
        r'(\d{4}-\d{2}-\d{2})\s+(\d{2}\.\d{2}\.\d{2})',
        # YYYY-MM-DD HH:mm:ss
        r'(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})',
        # YYYY-MM-DD_HH:mm:ss
        r'(\d{4}-\d{2}-\d{2})_(\d{2}:\d{2}:\d{2})',
        # YYYY-MM-DD at HH.mm.ss (для формата "Meet 2025-10-18 at 20.01.11")
        r'(\d{4}-\d{2}-\d{2})\s+at\s+(\d{2}\.\d{2}\.\d{2})',
        # YYYY-MM-DD at HH:mm:ss
        r'(\d{4}-\d{2}-\d{2})\s+at\s+(\d{2}:\d{2}:\d{2})',
        # YYYY-MM-DD at HH-mm-ss
        r'(\d{4}-\d{2}-\d{2})\s+at\s+(\d{2}-\d{2}-\d{2})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, name_without_ext)
        if match:
            date_part = match.group(1)
            time_part = match.group(2).replace('.', ':').replace('-', ':')
            
            try:
                # Пытаемся создать datetime объект
                datetime_str = f"{date_part}T{time_part}"
                parsed_dt = datetime.fromisoformat(datetime_str)
                return parsed_dt.isoformat()
            except ValueError:
                continue
    
    return None


def format_text_to_paragraphs(text: str, min_paragraph_length: int = 100) -> list[str]:
    """
    Разделяет текст на параграфы на основе пауз и длины предложений
    
    Args:
        text: Исходный текст
        min_paragraph_length: Минимальная длина параграфа
    
    Returns:
        Список параграфов
    """
    # Разделяем по предложениям
    sentences = []
    current_sentence = ""
    
    for char in text:
        current_sentence += char
        if char in '.!?':
            sentences.append(current_sentence.strip())
            current_sentence = ""
    
    if current_sentence.strip():
        sentences.append(current_sentence.strip())
    
    # Группируем предложения в параграфы
    paragraphs = []
    current_paragraph = ""
    
    for sentence in sentences:
        if not sentence:
            continue
            
        current_paragraph += sentence + " "
        
        # Если параграф достаточно длинный, завершаем его
        if len(current_paragraph.strip()) >= min_paragraph_length:
            paragraphs.append(current_paragraph.strip())
            current_paragraph = ""
    
    # Добавляем оставшийся текст как последний параграф
    if current_paragraph.strip():
        paragraphs.append(current_paragraph.strip())
    
    return paragraphs


def validate_audio_file(filename: str, content_type: Optional[str]) -> bool:
    """
    Проверяет, является ли файл аудио файлом
    
    Args:
        filename: Имя файла
        content_type: MIME тип файла
    
    Returns:
        True если файл является аудио файлом
    """
    audio_extensions = {'.mp3', '.wav', '.m4a', '.aac', '.flac', '.ogg', '.wma', '.aiff', '.au'}
    file_extension = os.path.splitext(filename or '')[1].lower()
    
    # Проверяем по MIME типу
    if content_type and content_type.startswith('audio/'):
        return True
    
    # Проверяем по расширению
    if file_extension in audio_extensions:
        return True
    
    return False

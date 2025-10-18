import os
import io
import base64
import tempfile
from typing import Optional
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from faster_whisper import WhisperModel
import subprocess
import json

app = FastAPI(title="Whisper Transcription API", version="1.0.0")

# Настройки из переменных окружения
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")
COMPUTE_TYPE = os.getenv("COMPUTE_TYPE", "int8")

# Инициализация модели Whisper
print(f"Loading Whisper model: {WHISPER_MODEL} with compute type: {COMPUTE_TYPE}")
model = WhisperModel(WHISPER_MODEL, compute_type=COMPUTE_TYPE)
print("Model loaded successfully!")

@app.get("/health")
async def health_check():
    """Проверка состояния API и модели"""
    return {
        "ok": True,
        "model": WHISPER_MODEL,
        "compute_type": COMPUTE_TYPE
    }

@app.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str = Form(default="ru")
):
    """
    Транскрибация аудиофайла
    
    Args:
        file: Аудиофайл для транскрибации
        language: Язык для распознавания (по умолчанию 'ru')
    
    Returns:
        JSON с распознанным текстом
    """
    try:
        # Проверяем тип файла
        if not file.content_type or not file.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="File must be an audio file")
        
        # Читаем содержимое файла
        audio_content = await file.read()
        
        # Создаем временный файл для обработки
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as temp_file:
            temp_file.write(audio_content)
            temp_file_path = temp_file.name
        
        try:
            # Выполняем транскрибацию
            segments, info = model.transcribe(
                temp_file_path,
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
                "success": True,
                "text": transcription_text.strip(),
                "segments": segments_list,
                "language": info.language,
                "language_probability": info.language_probability,
                "duration": info.duration
            }
            
        finally:
            # Удаляем временный файл
            os.unlink(temp_file_path)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

@app.post("/split")
async def split_audio(
    file: UploadFile = File(...),
    segment_sec: int = Form(default=600)
):
    """
    Разделение аудиофайла на части
    
    Args:
        file: Аудиофайл для разделения
        segment_sec: Длительность сегмента в секундах (по умолчанию 600)
    
    Returns:
        JSON со списком частей в base64
    """
    try:
        # Проверяем тип файла
        if not file.content_type or not file.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="File must be an audio file")
        
        # Читаем содержимое файла
        audio_content = await file.read()
        
        # Создаем временный файл для обработки
        input_filename = file.filename or "input_audio"
        input_extension = input_filename.split('.')[-1] if '.' in input_filename else 'mp3'
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{input_extension}") as temp_file:
            temp_file.write(audio_content)
            temp_input_path = temp_file.name
        
        try:
            # Получаем длительность аудио с помощью ffprobe
            duration_cmd = [
                "ffprobe", "-v", "quiet", "-print_format", "json", 
                "-show_format", temp_input_path
            ]
            
            result = subprocess.run(duration_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise HTTPException(status_code=500, detail="Failed to get audio duration")
            
            duration_data = json.loads(result.stdout)
            total_duration = float(duration_data["format"]["duration"])
            
            # Вычисляем количество сегментов
            num_segments = int(total_duration / segment_sec) + (1 if total_duration % segment_sec > 0 else 0)
            
            segments = []
            
            for i in range(num_segments):
                start_time = i * segment_sec
                end_time = min((i + 1) * segment_sec, total_duration)
                
                # Создаем временный файл для сегмента
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{input_extension}") as segment_file:
                    segment_path = segment_file.name
                
                try:
                    # Используем ffmpeg для нарезки
                    split_cmd = [
                        "ffmpeg", "-i", temp_input_path,
                        "-ss", str(start_time),
                        "-t", str(end_time - start_time),
                        "-c", "copy",
                        "-y",  # Перезаписывать файл без подтверждения
                        segment_path
                    ]
                    
                    result = subprocess.run(split_cmd, capture_output=True, text=True)
                    if result.returncode != 0:
                        raise HTTPException(status_code=500, detail=f"Failed to split segment {i+1}")
                    
                    # Читаем сегмент и конвертируем в base64
                    with open(segment_path, "rb") as f:
                        segment_data = f.read()
                    
                    segment_base64 = base64.b64encode(segment_data).decode('utf-8')
                    
                    segments.append({
                        "segment_number": i + 1,
                        "start_time": start_time,
                        "end_time": end_time,
                        "duration": end_time - start_time,
                        "data": segment_base64,
                        "filename": f"segment_{i+1}.{input_extension}"
                    })
                    
                finally:
                    # Удаляем временный файл сегмента
                    if os.path.exists(segment_path):
                        os.unlink(segment_path)
            
            return {
                "success": True,
                "total_duration": total_duration,
                "segment_duration": segment_sec,
                "num_segments": num_segments,
                "segments": segments
            }
            
        finally:
            # Удаляем временный входной файл
            os.unlink(temp_input_path)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio splitting failed: {str(e)}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

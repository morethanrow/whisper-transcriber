import os
import io
import base64
import tempfile
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from faster_whisper import WhisperModel
import subprocess
import json

# Импорты для диаризации
try:
    import librosa
    import numpy as np
    from sklearn.cluster import KMeans
    DIARIZATION_AVAILABLE = True
    print("Audio analysis libraries available for diarization!")
except ImportError:
    DIARIZATION_AVAILABLE = False
    print("Warning: Audio analysis libraries not available. Diarization will be disabled.")

app = FastAPI(title="Whisper Transcription API", version="1.0.0")

# Настройки из переменных окружения
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")
COMPUTE_TYPE = os.getenv("COMPUTE_TYPE", "int8")
PORT = int(os.getenv("PORT", 8000))

# Счетчик тестов для уникальных имен файлов
test_counter = 0

def generate_test_filename(prefix="test", extension="json"):
    """Генерирует уникальное имя файла для результатов тестов"""
    global test_counter
    test_counter += 1
    
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    
    filename = f"{prefix}_{test_counter:03d}_{timestamp}.{extension}"
    return os.path.join("test_results", filename)

# Инициализация модели Whisper
print(f"Loading Whisper model: {WHISPER_MODEL} with compute type: {COMPUTE_TYPE}")
model = WhisperModel(WHISPER_MODEL, compute_type=COMPUTE_TYPE)
print("Whisper model loaded successfully!")

# Функция простой диаризации на основе анализа аудио
def simple_diarization(audio_path, min_speakers=1, max_speakers=5):
    """
    Простая диаризация на основе анализа акустических характеристик
    """
    try:
        # Загружаем аудио
        y, sr = librosa.load(audio_path, sr=16000)
        
        # 1. Сегментация по паузам
        segments = detect_speech_segments(y, sr)
        
        # 2. Извлечение акустических признаков для каждого сегмента
        features = []
        segment_times = []
        
        for start, end in segments:
            segment_audio = y[start:end]
            if len(segment_audio) > 0.1 * sr:  # Минимум 100мс
                # Извлекаем признаки
                feature_vector = extract_voice_features(segment_audio, sr)
                if feature_vector is not None:
                    features.append(feature_vector)
                    segment_times.append((start/sr, end/sr))
        
        if len(features) < 2:
            return create_single_speaker_result(segment_times)
        
        # 3. Кластеризация по голосовым характеристикам
        features_array = np.array(features)
        n_speakers = min(max_speakers, max(min_speakers, len(features)//3))
        
        if n_speakers > len(features):
            n_speakers = len(features)
        
        kmeans = KMeans(n_clusters=n_speakers, random_state=42, n_init=10)
        speaker_labels = kmeans.fit_predict(features_array)
        
        # 4. Формирование результата
        speakers = {}
        segments_result = []
        
        for i, (start_time, end_time) in enumerate(segment_times):
            speaker_id = f"SPEAKER_{speaker_labels[i]:02d}"
            
            if speaker_id not in speakers:
                speakers[speaker_id] = {
                    "speaker_id": speaker_id,
                    "total_duration": 0,
                    "segments_count": 0
                }
            
            duration = end_time - start_time
            segment = {
                "speaker": speaker_id,
                "start": start_time,
                "end": end_time,
                "duration": duration
            }
            
            segments_result.append(segment)
            speakers[speaker_id]["total_duration"] += duration
            speakers[speaker_id]["segments_count"] += 1
        
        total_duration = max(seg["end"] for seg in segments_result) if segments_result else 0
        
        return {
            "success": True,
            "total_duration": total_duration,
            "num_speakers": len(speakers),
            "speakers": list(speakers.values()),
            "segments": segments_result
        }
        
    except Exception as e:
        print(f"Error in simple diarization: {e}")
        return None

def detect_speech_segments(y, sr, frame_length=2048, hop_length=512):
    """Обнаружение речевых сегментов по паузам"""
    # Вычисляем энергию сигнала
    energy = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
    
    # Нормализуем энергию
    energy = energy / np.max(energy)
    
    # Порог для определения речи (настраиваемый параметр)
    threshold = 0.01
    
    # Находим речевые сегменты
    speech_frames = energy > threshold
    
    # Находим границы сегментов
    segments = []
    in_speech = False
    start_frame = 0
    
    for i, is_speech in enumerate(speech_frames):
        if is_speech and not in_speech:
            start_frame = i
            in_speech = True
        elif not is_speech and in_speech:
            # Минимальная длительность сегмента (0.5 секунды)
            min_duration_frames = int(0.5 * sr / hop_length)
            if i - start_frame > min_duration_frames:
                start_sample = start_frame * hop_length
                end_sample = i * hop_length
                segments.append((start_sample, end_sample))
            in_speech = False
    
    # Обрабатываем последний сегмент
    if in_speech:
        min_duration_frames = int(0.5 * sr / hop_length)
        if len(speech_frames) - start_frame > min_duration_frames:
            start_sample = start_frame * hop_length
            end_sample = len(speech_frames) * hop_length
            segments.append((start_sample, end_sample))
    
    return segments

def extract_voice_features(y, sr):
    """Извлечение акустических признаков голоса"""
    try:
        features = []
        
        # 1. Частота основного тона (F0)
        f0, voiced_flag, voiced_probs = librosa.pyin(y, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'))
        f0_mean = np.nanmean(f0) if not np.all(np.isnan(f0)) else 0
        f0_std = np.nanstd(f0) if not np.all(np.isnan(f0)) else 0
        features.extend([f0_mean, f0_std])
        
        # 2. Спектральные центроиды
        spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        features.extend([np.mean(spectral_centroids), np.std(spectral_centroids)])
        
        # 3. Спектральная полоса пропускания
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
        features.extend([np.mean(spectral_bandwidth), np.std(spectral_bandwidth)])
        
        # 4. Zero Crossing Rate
        zcr = librosa.feature.zero_crossing_rate(y)[0]
        features.extend([np.mean(zcr), np.std(zcr)])
        
        # 5. MFCC (первые 4 коэффициента)
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=4)
        for i in range(4):
            features.extend([np.mean(mfccs[i]), np.std(mfccs[i])])
        
        # 6. Энергия
        rms = librosa.feature.rms(y=y)[0]
        features.extend([np.mean(rms), np.std(rms)])
        
        return np.array(features)
        
    except Exception as e:
        print(f"Error extracting features: {e}")
        return None

def create_single_speaker_result(segment_times):
    """Создает результат для одного говорящего"""
    speakers = {
        "SPEAKER_00": {
            "speaker_id": "SPEAKER_00",
            "total_duration": 0,
            "segments_count": 0
        }
    }
    
    segments = []
    total_duration = 0
    
    for start_time, end_time in segment_times:
        duration = end_time - start_time
        segment = {
            "speaker": "SPEAKER_00",
            "start": start_time,
            "end": end_time,
            "duration": duration
        }
        segments.append(segment)
        speakers["SPEAKER_00"]["total_duration"] += duration
        speakers["SPEAKER_00"]["segments_count"] += 1
        total_duration = max(total_duration, end_time)
    
    return {
        "success": True,
        "total_duration": total_duration,
        "num_speakers": 1,
        "speakers": list(speakers.values()),
        "segments": segments
    }

# Инициализация модели диаризации
diarization_model = simple_diarization if DIARIZATION_AVAILABLE else None

@app.get("/health")
async def health_check():
    """Проверка состояния API и модели"""
    return {
        "ok": True,
        "model": WHISPER_MODEL,
        "compute_type": COMPUTE_TYPE,
        "diarization_available": DIARIZATION_AVAILABLE
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
        # Проверяем тип файла (более гибкая проверка)
        allowed_extensions = {'.mp3', '.wav', '.m4a', '.flac', '.ogg', '.aac', '.wma', '.mp4', '.avi', '.mov'}
        file_extension = os.path.splitext(file.filename or '')[1].lower()
        
        if not file.content_type or (not file.content_type.startswith('audio/') and not file.content_type.startswith('video/') and file_extension not in allowed_extensions):
            raise HTTPException(status_code=400, detail=f"File must be an audio file. Got: {file.content_type}, extension: {file_extension}")
        
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
        # Проверяем тип файла (более гибкая проверка)
        allowed_extensions = {'.mp3', '.wav', '.m4a', '.flac', '.ogg', '.aac', '.wma', '.mp4', '.avi', '.mov'}
        file_extension = os.path.splitext(file.filename or '')[1].lower()
        
        if not file.content_type or (not file.content_type.startswith('audio/') and not file.content_type.startswith('video/') and file_extension not in allowed_extensions):
            raise HTTPException(status_code=400, detail=f"File must be an audio file. Got: {file.content_type}, extension: {file_extension}")
        
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
            # Проверяем локальную установку ffprobe, иначе используем системную
            local_ffprobe = os.path.join(os.getcwd(), "bin", "ffprobe")
            ffprobe_path = local_ffprobe if os.path.exists(local_ffprobe) else "ffprobe"
            duration_cmd = [
                ffprobe_path, "-v", "quiet", "-print_format", "json", 
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
                    # Проверяем локальную установку ffmpeg, иначе используем системную
                    local_ffmpeg = os.path.join(os.getcwd(), "bin", "ffmpeg")
                    ffmpeg_path = local_ffmpeg if os.path.exists(local_ffmpeg) else "ffmpeg"
                    split_cmd = [
                        ffmpeg_path, "-i", temp_input_path,
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

@app.post("/diarize")
async def diarize_audio(
    file: UploadFile = File(...),
    min_speakers: int = Form(default=1),
    max_speakers: int = Form(default=10)
):
    """
    Диаризация аудиофайла (разделение на говорящих)
    
    Args:
        file: Аудиофайл для диаризации
        min_speakers: Минимальное количество говорящих
        max_speakers: Максимальное количество говорящих
    
    Returns:
        JSON с информацией о говорящих и временных сегментах
    """
    if not DIARIZATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Diarization not available. Please install pyannote.audio")
    
    try:
        # Проверяем тип файла (более гибкая проверка)
        allowed_extensions = {'.mp3', '.wav', '.m4a', '.flac', '.ogg', '.aac', '.wma', '.mp4', '.avi', '.mov'}
        file_extension = os.path.splitext(file.filename or '')[1].lower()
        
        if not file.content_type or (not file.content_type.startswith('audio/') and not file.content_type.startswith('video/') and file_extension not in allowed_extensions):
            raise HTTPException(status_code=400, detail=f"File must be an audio file. Got: {file.content_type}, extension: {file_extension}")
        
        # Читаем содержимое файла
        audio_content = await file.read()
        
        # Создаем временный файл для обработки
        input_filename = file.filename or "input_audio"
        input_extension = input_filename.split('.')[-1] if '.' in input_filename else 'mp3'
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{input_extension}") as temp_file:
            temp_file.write(audio_content)
            temp_input_path = temp_file.name
        
        try:
            # Выполняем диаризацию
            if diarization_model is None:
                raise HTTPException(status_code=503, detail="Diarization model not loaded")
            diarization_result = diarization_model(temp_input_path, min_speakers=min_speakers, max_speakers=max_speakers)
            
            if diarization_result is None:
                raise HTTPException(status_code=500, detail="Diarization failed")
            
            # Возвращаем результат диаризации
            return diarization_result
            
        finally:
            # Удаляем временный файл
            os.unlink(temp_input_path)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Diarization failed: {str(e)}")

@app.post("/transcribe_with_diarization")
async def transcribe_with_diarization(
    file: UploadFile = File(...),
    language: str = Form(default="ru"),
    min_speakers: int = Form(default=1),
    max_speakers: int = Form(default=10)
):
    """
    Транскрибация с диаризацией (комбинированный эндпоинт)
    
    Args:
        file: Аудиофайл для обработки
        language: Язык для распознавания
        min_speakers: Минимальное количество говорящих
        max_speakers: Максимальное количество говорящих
    
    Returns:
        JSON с транскрипцией и информацией о говорящих
    """
    if not DIARIZATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Diarization not available. Please install pyannote.audio")
    
    try:
        # Проверяем тип файла
        allowed_extensions = {'.mp3', '.wav', '.m4a', '.flac', '.ogg', '.aac', '.wma', '.mp4', '.avi', '.mov'}
        file_extension = os.path.splitext(file.filename or '')[1].lower()
        
        if not file.content_type or (not file.content_type.startswith('audio/') and not file.content_type.startswith('video/') and file_extension not in allowed_extensions):
            raise HTTPException(status_code=400, detail=f"File must be an audio file. Got: {file.content_type}, extension: {file_extension}")
        
        # Читаем содержимое файла
        audio_content = await file.read()
        
        # Создаем временный файл для обработки
        input_filename = file.filename or "input_audio"
        input_extension = input_filename.split('.')[-1] if '.' in input_filename else 'mp3'
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{input_extension}") as temp_file:
            temp_file.write(audio_content)
            temp_input_path = temp_file.name
        
        try:
            # Выполняем диаризацию
            if diarization_model is None:
                raise HTTPException(status_code=503, detail="Diarization model not loaded")
            diarization_result = diarization_model(temp_input_path, min_speakers=min_speakers, max_speakers=max_speakers)
            
            if diarization_result is None:
                raise HTTPException(status_code=500, detail="Diarization failed")
            
            # Выполняем транскрибацию
            segments, info = model.transcribe(
                temp_input_path,
                language=language if language != "auto" else None,
                beam_size=5
            )
            
            # Объединяем результаты
            transcription_segments = []
            for segment in segments:
                transcription_segments.append({
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip()
                })
            
            # Определяем говорящего для каждого сегмента транскрипции
            speaker_segments = []
            for seg in transcription_segments:
                # Находим говорящего для этого временного интервала
                speaker = "UNKNOWN"
                for diarization_seg in diarization_result["segments"]:
                    if (diarization_seg["start"] <= seg["start"] < diarization_seg["end"] or 
                        diarization_seg["start"] < seg["end"] <= diarization_seg["end"]):
                        speaker = diarization_seg["speaker"]
                        break
                
                speaker_segments.append({
                    "speaker": speaker,
                    "start": seg["start"],
                    "end": seg["end"],
                    "text": seg["text"]
                })
            
            # Группируем по говорящим
            speakers = {}
            for seg in speaker_segments:
                speaker_id = seg["speaker"]
                if speaker_id not in speakers:
                    speakers[speaker_id] = {
                        "speaker_id": speaker_id,
                        "text": "",
                        "segments": []
                    }
                
                speakers[speaker_id]["text"] += seg["text"] + " "
                speakers[speaker_id]["segments"].append({
                    "start": seg["start"],
                    "end": seg["end"],
                    "text": seg["text"]
                })
            
            # Полный текст
            full_text = " ".join(seg["text"] for seg in transcription_segments)
            
            return {
                "success": True,
                "text": full_text.strip(),
                "language": info.language,
                "language_probability": info.language_probability,
                "duration": info.duration,
                "num_speakers": len(speakers),
                "speakers": list(speakers.values()),
                "segments": speaker_segments
            }
            
        finally:
            # Удаляем временный файл
            os.unlink(temp_input_path)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription with diarization failed: {str(e)}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

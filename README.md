# Whisper Transcription API

Бесплатный API для транскрибации аудио с помощью open-source модели Whisper от OpenAI. Проект использует библиотеку `faster-whisper` для быстрой работы на CPU и полностью работает локально без обращения к платным API.

## Возможности

- 🎵 **Транскрибация аудио** - преобразование аудиофайлов в текст
- ✂️ **Разделение аудио** - нарезка больших файлов на части с помощью ffmpeg
- 🌍 **Многоязычность** - поддержка различных языков (по умолчанию русский)
- 🚀 **Готов к деплою** - оптимизирован для Railway и других облачных платформ
- 💰 **Полностью бесплатно** - никаких платных API, все работает локально

## API Эндпоинты

### GET /health
Проверка состояния API и модели.

**Ответ:**
```json
{
  "ok": true,
  "model": "small",
  "compute_type": "int8"
}
```

### POST /transcribe
Транскрибация аудиофайла.

**Параметры:**
- `file` (multipart/form-data) - аудиофайл для транскрибации
- `language` (form-data) - язык для распознавания (по умолчанию "ru")

**Ответ:**
```json
{
  "success": true,
  "text": "Распознанный текст...",
  "segments": [
    {
      "start": 0.0,
      "end": 5.2,
      "text": "Первая часть текста"
    }
  ],
  "language": "ru",
  "language_probability": 0.99,
  "duration": 30.5
}
```

### POST /split
Разделение аудиофайла на части.

**Параметры:**
- `file` (multipart/form-data) - аудиофайл для разделения
- `segment_sec` (form-data) - длительность сегмента в секундах (по умолчанию 600)

**Ответ:**
```json
{
  "success": true,
  "total_duration": 1800.0,
  "segment_duration": 600,
  "num_segments": 3,
  "segments": [
    {
      "segment_number": 1,
      "start_time": 0.0,
      "end_time": 600.0,
      "duration": 600.0,
      "data": "base64_encoded_audio_data...",
      "filename": "segment_1.mp3"
    }
  ]
}
```

## Переменные окружения

- `WHISPER_MODEL` - модель Whisper для использования (по умолчанию "small")
- `COMPUTE_TYPE` - тип вычислений (по умолчанию "int8")
- `PORT` - порт для запуска сервера (по умолчанию 8000)

## Доступные модели Whisper

- `tiny` - самая быстрая, наименьшая точность
- `base` - быстрая, хорошая точность
- `small` - сбалансированная скорость и точность (рекомендуется)
- `medium` - медленная, высокая точность
- `large` - самая медленная, максимальная точность

## Локальный запуск

### Предварительные требования

- Python 3.11+
- ffmpeg (для разделения аудио)

### Установка ffmpeg

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Windows:**
Скачайте с [официального сайта](https://ffmpeg.org/download.html) и добавьте в PATH.

### Запуск

1. Клонируйте репозиторий:
```bash
git clone <your-repo-url>
cd transcripter
```

2. Создайте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Запустите приложение:
```bash
python app.py
```

Приложение будет доступно по адресу: http://localhost:8000

### Тестирование API

**Проверка здоровья:**
```bash
curl http://localhost:8000/health
```

**Транскрибация:**
```bash
curl -X POST "http://localhost:8000/transcribe" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@your_audio_file.mp3" \
  -F "language=ru"
```

**Разделение аудио:**
```bash
curl -X POST "http://localhost:8000/split" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@your_audio_file.mp3" \
  -F "segment_sec=300"
```

## Деплой на Railway

### Метод 1: Через GitHub

1. Загрузите код в GitHub репозиторий
2. Зайдите на [Railway](https://railway.app)
3. Нажмите "New Project" → "Deploy from GitHub repo"
4. Выберите ваш репозиторий
5. Railway автоматически определит Python проект и создаст Dockerfile
6. Настройте переменные окружения в настройках проекта:
   - `WHISPER_MODEL`: `small` (или другую модель)
   - `COMPUTE_TYPE`: `int8`

### Метод 2: Через Railway CLI

1. Установите Railway CLI:
```bash
npm install -g @railway/cli
```

2. Войдите в аккаунт:
```bash
railway login
```

3. Инициализируйте проект:
```bash
railway init
```

4. Задеплойте:
```bash
railway up
```

### Настройка переменных окружения на Railway

В панели управления Railway:
1. Перейдите в Settings → Variables
2. Добавьте переменные:
   - `WHISPER_MODEL` = `small`
   - `COMPUTE_TYPE` = `int8`

## Деплой на других платформах

### Docker

```bash
# Сборка образа
docker build -t whisper-api .

# Запуск контейнера
docker run -p 8000:8000 -e WHISPER_MODEL=small whisper-api
```

### Heroku

1. Создайте `Procfile`:
```
web: uvicorn app:app --host 0.0.0.0 --port $PORT
```

2. Добавьте buildpack для ffmpeg:
```bash
heroku buildpacks:add https://github.com/jonathanong/heroku-buildpack-ffmpeg-latest.git
heroku buildpacks:add heroku/python
```

3. Задеплойте:
```bash
git push heroku main
```

## Производительность

- **Модель `small`** рекомендуется для большинства случаев
- **`int8`** compute type обеспечивает хорошую производительность на CPU
- Первый запрос может быть медленным из-за загрузки модели
- Последующие запросы работают значительно быстрее

## Поддерживаемые форматы аудио

- MP3
- WAV
- M4A
- FLAC
- OGG
- И другие форматы, поддерживаемые ffmpeg

## Ограничения

- Максимальный размер файла зависит от платформы деплоя
- Railway: обычно до 100MB
- Для больших файлов используйте эндпоинт `/split`

## Устранение неполадок

### Ошибка "ffmpeg not found"
Убедитесь, что ffmpeg установлен и доступен в PATH.

### Медленная работа
- Используйте модель `tiny` или `base` для ускорения
- Установите `COMPUTE_TYPE=int8`

### Ошибки памяти
- Используйте модель меньшего размера
- Разделяйте большие файлы на части

## Лицензия

MIT License

## Вклад в проект

Приветствуются pull requests и issues!

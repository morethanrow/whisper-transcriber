# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем системные зависимости для PyAV и ffmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    pkg-config \
    libavformat-dev \
    libavcodec-dev \
    libavdevice-dev \
    libavutil-dev \
    libswscale-dev \
    libswresample-dev \
    libavfilter-dev \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код приложения
COPY . .

# Создаем директорию для результатов тестов
RUN mkdir -p test_result

# Открываем порт (Railway автоматически устанавливает PORT)
EXPOSE $PORT

# Запускаем приложение
CMD ["python", "app.py"]

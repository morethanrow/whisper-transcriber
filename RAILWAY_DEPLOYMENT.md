# Развертывание на Railway

## Пошаговая инструкция

### 1. Подготовка репозитория

1. **Создайте репозиторий на GitHub:**
   - Перейдите на https://github.com/new
   - Название: `audio-transcripter` (или любое другое)
   - Сделайте репозиторий публичным или приватным
   - НЕ добавляйте README, .gitignore или лицензию (у нас уже есть)

2. **Загрузите код в GitHub:**
```bash
# Инициализируйте git (если еще не сделано)
git init

# Добавьте все файлы
git add .

# Сделайте первый коммит
git commit -m "Initial commit: Audio Transcription Service"

# Добавьте удаленный репозиторий (замените YOUR_USERNAME на ваш GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/audio-transcripter.git

# Загрузите код
git push -u origin main
```

### 2. Развертывание на Railway

1. **Зарегистрируйтесь на Railway:**
   - Перейдите на https://railway.app
   - Нажмите "Start a New Project"
   - Войдите через GitHub

2. **Создайте новый проект:**
   - Нажмите "Deploy from GitHub repo"
   - Выберите ваш репозиторий `audio-transcripter`
   - Railway автоматически определит, что это Python проект

3. **Настройте переменные окружения:**
   - В панели Railway перейдите в Settings → Variables
   - Добавьте переменные:
     ```
     WHISPER_MODEL=small
     COMPUTE_TYPE=int8
     PORT=8000
     ```

4. **Дождитесь развертывания:**
   - Railway автоматически соберет и развернет ваш сервис
   - Процесс займет 5-10 минут
   - Вы получите публичный URL вида: `https://your-app-name.up.railway.app`

### 3. Тестирование развернутого сервиса

1. **Проверьте health endpoint:**
```bash
curl https://your-app-name.up.railway.app/health
```

2. **Протестируйте транскрибацию:**
```bash
curl -X POST "https://your-app-name.up.railway.app/transcribe" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@your-audio-file.m4a" \
  -F "language=ru" \
  -F "save_result=true"
```

### 4. Получение URL для n8n

После успешного развертывания вы получите:
- **Основной URL:** `https://your-app-name.up.railway.app`
- **Health check:** `https://your-app-name.up.railway.app/health`
- **Transcribe endpoint:** `https://your-app-name.up.railway.app/transcribe`
- **Test results:** `https://your-app-name.up.railway.app/test-results`

## Важные моменты

### ⚠️ Ограничения Railway:
- **Бесплатный план:** 500 часов в месяц, 1GB RAM, 1GB диск
- **Таймаут запросов:** 5 минут максимум
- **Автоматическое отключение:** после 5 минут неактивности

### 💡 Рекомендации:
- Для продакшена рассмотрите платный план Railway
- Или используйте другие платформы: Render, Fly.io, Heroku
- Настройте мониторинг и логирование

### 🔧 Настройка для продакшена:
1. **Увеличьте лимиты памяти** в Railway
2. **Настройте автодеплой** из GitHub
3. **Добавьте мониторинг** (например, Sentry)
4. **Настройте резервное копирование** результатов

## Следующий шаг: Интеграция с n8n

После развертывания переходите к настройке n8n workflow для саммаризации!

# Быстрый деплой на Railway

## ✅ Проект готов к деплою!

### Что исправлено:
1. ✅ **Dockerfile** - добавлены все необходимые системные зависимости для PyAV
2. ✅ **requirements.txt** - обновлены версии для лучшей совместимости
3. ✅ **Локальное тестирование** - приложение успешно запускается и работает
4. ✅ **API тестирование** - эндпоинт `/health` возвращает корректный ответ

### Шаги для деплоя:

1. **Загрузите код в GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin <your-github-repo-url>
   git push -u origin main
   ```

2. **Создайте проект на Railway:**
   - Зайдите на https://railway.app
   - Нажмите "New Project" → "Deploy from GitHub repo"
   - Выберите ваш репозиторий

3. **Настройте переменные окружения:**
   - В настройках проекта добавьте:
     - `WHISPER_MODEL` = `small`
     - `COMPUTE_TYPE` = `int8`

4. **Деплой запустится автоматически!**

### Структура проекта:
```
.
├── app.py              # FastAPI приложение
├── Dockerfile          # Контейнер с системными зависимостями
├── requirements.txt    # Python зависимости
├── README.md           # Документация
└── .dockerignore       # Исключения для Docker
```

### Тестирование после деплоя:
```bash
# Проверка здоровья
curl https://your-app.railway.app/health

# Транскрибация (замените URL на ваш)
curl -X POST "https://your-app.railway.app/transcribe" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@audio.mp3" \
  -F "language=ru"
```

### Возможные проблемы и решения:

1. **Ошибка сборки PyAV** - ✅ Исправлено в Dockerfile
2. **Медленная загрузка модели** - Нормально для первого запроса
3. **Превышение лимитов памяти** - Используйте модель `tiny` или `base`

Проект полностью готов к продакшену! 🚀

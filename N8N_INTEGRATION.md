# Интеграция с N8N

Этот сервис готов для использования с n8n. Ниже приведены примеры настройки workflow'ов.

## Базовый workflow для транскрибации

### 1. HTTP Request Node для транскрибации

**Настройки:**
- Method: `POST`
- URL: `http://your-service-url/transcribe`
- Body Type: `Form-Data`
- Form Fields:
  - `file`: [Binary Data] - аудио файл
  - `language`: `ru` (или другой язык)
  - `save_result`: `true`

### 2. Обработка ответа

Ответ будет содержать:
```json
{
  "info": {
    "filename": "2025-10-18_20-01-11_audio_file.mp3",
    "recorded_at": "2025-10-18T20:01:11",
    "duration_sec": 30.5,
    "model": "whisper-small:int8"
  },
  "result": {
    "status": "ok",
    "language": "ru",
    "text": "Полный распознанный текст...",
    "paragraphs": [
      "Первый параграф текста.",
      "Второй параграф текста."
    ]
  },
  "saved_to": "/path/to/test_result/test_0001_18.01.2025_22.47.json",
  "test_number": 1
}
```

### 3. Извлечение данных

Используйте следующие выражения в n8n:

- **Полный текст**: `{{ $json.result.text }}`
- **Параграфы**: `{{ $json.result.paragraphs }}`
- **Дата/время записи**: `{{ $json.info.recorded_at }}`
- **Длительность**: `{{ $json.info.duration_sec }}`
- **Номер теста**: `{{ $json.test_number }}`
- **Статус**: `{{ $json.result.status }}`
- **Язык**: `{{ $json.result.language }}`
- **Модель**: `{{ $json.info.model }}`

## Workflow для получения сохраненных результатов

### 1. HTTP Request для списка результатов

**Настройки:**
- Method: `GET`
- URL: `http://your-service-url/test-results`

### 2. HTTP Request для конкретного результата

**Настройки:**
- Method: `GET`
- URL: `http://your-service-url/test-results/{{ $json.test_number }}`

## Пример полного workflow

```json
{
  "nodes": [
    {
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "parameters": {
        "path": "transcribe",
        "httpMethod": "POST"
      }
    },
    {
      "name": "Transcribe Audio",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "POST",
        "url": "http://your-service-url/transcribe",
        "bodyType": "multipart-form-data",
        "bodyParameters": {
          "parameters": [
            {
              "name": "file",
              "value": "={{ $binary.data }}"
            },
            {
              "name": "language",
              "value": "ru"
            },
            {
              "name": "save_result",
              "value": "true"
            }
          ]
        }
      }
    },
    {
      "name": "Process Result",
      "type": "n8n-nodes-base.function",
      "parameters": {
        "functionCode": "// Извлекаем основные данные\nconst result = items[0].json;\n\nreturn [{\n  json: {\n    status: result.result.status,\n    text: result.result.text,\n    paragraphs: result.result.paragraphs,\n    recordedAt: result.info.recorded_at,\n    duration: result.info.duration_sec,\n    testNumber: result.test_number,\n    filename: result.info.filename,\n    model: result.info.model,\n    language: result.result.language\n  }\n}];"
      }
    }
  ],
  "connections": {
    "Webhook": {
      "main": [["Transcribe Audio"]]\n    },\n    "Transcribe Audio": {\n      "main": [["Process Result"]]\n    }\n  }\n}
```

## Переменные окружения для n8n

Рекомендуется создать переменные окружения в n8n:

- `TRANSCRIPTION_SERVICE_URL`: URL вашего сервиса транскрибации
- `DEFAULT_LANGUAGE`: Язык по умолчанию (например, `ru`)

## Обработка ошибок

Добавьте обработку ошибок в ваш workflow:

```javascript
// В Function node для обработки ошибок
if (items[0].json.result.status !== 'ok') {
  throw new Error(`Transcription failed: ${items[0].json.result.error_message || 'Unknown error'}`);
}
```

## Мониторинг

Для мониторинга состояния сервиса используйте:

- **Health Check**: `GET /health`
- **Список результатов**: `GET /test-results`

## Примеры использования

### 1. Простая транскрибация
```bash
curl -X POST "http://your-service-url/transcribe" \\
  -H "Content-Type: multipart/form-data" \\
  -F "file=@audio.mp3" \\
  -F "language=ru"
```

### 2. Получение результатов
```bash
# Список всех результатов
curl "http://your-service-url/test-results"

# Конкретный результат
curl "http://your-service-url/test-results/1"
```

## Рекомендации

1. **Используйте webhook** для получения уведомлений о завершении транскрибации
2. **Сохраняйте test_number** для последующего получения результатов
3. **Обрабатывайте большие файлы** - сервис автоматически нарезает их на сегменты
4. **Мониторьте производительность** через health check эндпоинт
5. **Используйте правильный язык** для лучшего качества распознавания

# Интеграция с n8n для саммаризации

## Обзор workflow

После развертывания сервиса на Railway, вы можете создать n8n workflow для автоматической саммаризации аудио:

```
Аудио файл → Транскрибация → Саммаризация → Сохранение результата
```

## Настройка n8n Workflow

### 1. Создание нового Workflow

1. **Откройте n8n**
2. **Создайте новый workflow**
3. **Добавьте следующие ноды:**

### 2. Конфигурация нод

#### **Нода 1: Webhook (Trigger)**
```json
{
  "name": "Audio Upload Webhook",
  "type": "n8n-nodes-base.webhook",
  "parameters": {
    "path": "audio-upload",
    "httpMethod": "POST",
    "responseMode": "responseNode"
  }
}
```

#### **Нода 2: HTTP Request (Транскрибация)**
```json
{
  "name": "Transcribe Audio",
  "type": "n8n-nodes-base.httpRequest",
  "parameters": {
    "url": "https://your-app-name.up.railway.app/transcribe",
    "method": "POST",
    "sendHeaders": true,
    "headerParameters": {
      "parameters": [
        {
          "name": "Content-Type",
          "value": "multipart/form-data"
        }
      ]
    },
    "sendBody": true,
    "bodyParameters": {
      "parameters": [
        {
          "name": "file",
          "value": "={{ $json.file }}"
        },
        {
          "name": "language",
          "value": "ru"
        },
        {
          "name": "save_result",
          "value": "false"
        }
      ]
    }
  }
}
```

#### **Нода 3: HTTP Request (Саммаризация)**
```json
{
  "name": "Summarize Text",
  "type": "n8n-nodes-base.httpRequest",
  "parameters": {
    "url": "https://api.openai.com/v1/chat/completions",
    "method": "POST",
    "sendHeaders": true,
    "headerParameters": {
      "parameters": [
        {
          "name": "Authorization",
          "value": "Bearer YOUR_OPENAI_API_KEY"
        },
        {
          "name": "Content-Type",
          "value": "application/json"
        }
      ]
    },
    "sendBody": true,
    "bodyParameters": {
      "parameters": [
        {
          "name": "model",
          "value": "gpt-3.5-turbo"
        },
        {
          "name": "messages",
          "value": [
            {
              "role": "system",
              "content": "Ты - эксперт по созданию кратких и информативных саммари. Создай структурированное резюме на русском языке."
            },
            {
              "role": "user",
              "content": "Создай краткое резюме следующего текста:\n\n{{ $json.result.text }}"
            }
          ]
        },
        {
          "name": "max_tokens",
          "value": 1000
        },
        {
          "name": "temperature",
          "value": 0.3
        }
      ]
    }
  }
}
```

#### **Нода 4: Set (Форматирование результата)**
```json
{
  "name": "Format Result",
  "type": "n8n-nodes-base.set",
  "parameters": {
    "values": {
      "string": [
        {
          "name": "original_filename",
          "value": "={{ $('Transcribe Audio').item.json.info.filename }}"
        },
        {
          "name": "recorded_at",
          "value": "={{ $('Transcribe Audio').item.json.info.recorded_at }}"
        },
        {
          "name": "duration_sec",
          "value": "={{ $('Transcribe Audio').item.json.info.duration_sec }}"
        },
        {
          "name": "transcription_text",
          "value": "={{ $('Transcribe Audio').item.json.result.text }}"
        },
        {
          "name": "summary",
          "value": "={{ $('Summarize Text').item.json.choices[0].message.content }}"
        },
        {
          "name": "language",
          "value": "={{ $('Transcribe Audio').item.json.result.language }}"
        },
        {
          "name": "paragraphs_count",
          "value": "={{ $('Transcribe Audio').item.json.result.paragraphs.length }}"
        }
      ]
    }
  }
}
```

#### **Нода 5: HTTP Request (Сохранение в Google Sheets)**
```json
{
  "name": "Save to Google Sheets",
  "type": "n8n-nodes-base.googleSheets",
  "parameters": {
    "operation": "appendOrUpdate",
    "documentId": "YOUR_GOOGLE_SHEET_ID",
    "sheetName": "Transcriptions",
    "columns": {
      "mappingMode": "defineBelow",
      "value": {
        "Timestamp": "={{ new Date().toISOString() }}",
        "Filename": "={{ $json.original_filename }}",
        "Recorded At": "={{ $json.recorded_at }}",
        "Duration (sec)": "={{ $json.duration_sec }}",
        "Language": "={{ $json.language }}",
        "Paragraphs Count": "={{ $json.paragraphs_count }}",
        "Transcription": "={{ $json.transcription_text }}",
        "Summary": "={{ $json.summary }}"
      }
    }
  }
}
```

#### **Нода 6: Respond to Webhook**
```json
{
  "name": "Response",
  "type": "n8n-nodes-base.respondToWebhook",
  "parameters": {
    "respondWith": "json",
    "responseBody": {
      "success": true,
      "message": "Audio processed successfully",
      "data": {
        "filename": "={{ $json.original_filename }}",
        "summary": "={{ $json.summary }}",
        "duration": "={{ $json.duration_sec }}",
        "language": "={{ $json.language }}"
      }
    }
  }
}
```

### 3. Альтернативные варианты саммаризации

#### **Вариант A: Использование Claude API**
```json
{
  "name": "Claude Summarize",
  "type": "n8n-nodes-base.httpRequest",
  "parameters": {
    "url": "https://api.anthropic.com/v1/messages",
    "method": "POST",
    "sendHeaders": true,
    "headerParameters": {
      "parameters": [
        {
          "name": "x-api-key",
          "value": "YOUR_CLAUDE_API_KEY"
        },
        {
          "name": "Content-Type",
          "value": "application/json"
        },
        {
          "name": "anthropic-version",
          "value": "2023-06-01"
        }
      ]
    },
    "sendBody": true,
    "bodyParameters": {
      "parameters": [
        {
          "name": "model",
          "value": "claude-3-sonnet-20240229"
        },
        {
          "name": "max_tokens",
          "value": 1000
        },
        {
          "name": "messages",
          "value": [
            {
              "role": "user",
              "content": "Создай краткое резюме следующего текста на русском языке:\n\n{{ $json.result.text }}"
            }
          ]
        }
      ]
    }
  }
}
```

#### **Вариант B: Локальная саммаризация (если есть GPU)**
```json
{
  "name": "Local Summarize",
  "type": "n8n-nodes-base.httpRequest",
  "parameters": {
    "url": "http://localhost:7860/api/v1/generate",
    "method": "POST",
    "sendBody": true,
    "bodyParameters": {
      "parameters": [
        {
          "name": "prompt",
          "value": "Создай краткое резюме:\n{{ $json.result.text }}"
        },
        {
          "name": "max_new_tokens",
          "value": 500
        }
      ]
    }
  }
}
```

## Тестирование Workflow

### 1. Тест через cURL
```bash
curl -X POST "https://your-n8n-instance.com/webhook/audio-upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test-audio.m4a"
```

### 2. Тест через Postman
1. **Создайте POST запрос**
2. **URL:** `https://your-n8n-instance.com/webhook/audio-upload`
3. **Body:** form-data
4. **Добавьте файл:** `file` → выберите аудио файл
5. **Отправьте запрос**

## Мониторинг и логирование

### 1. Добавьте ноду для логирования ошибок
```json
{
  "name": "Error Handler",
  "type": "n8n-nodes-base.if",
  "parameters": {
    "conditions": {
      "string": [
        {
          "value1": "={{ $json.error }}",
          "operation": "isNotEmpty"
        }
      ]
    }
  }
}
```

### 2. Настройте уведомления
- **Email уведомления** при ошибках
- **Slack/Discord** уведомления о завершении обработки
- **Telegram** бот для мониторинга

## Оптимизация производительности

### 1. Параллельная обработка
- Используйте **Split In Batches** для обработки нескольких файлов
- Настройте **Queue Mode** для больших объемов

### 2. Кэширование
- Добавьте проверку существующих результатов
- Используйте **Redis** для кэширования саммари

### 3. Масштабирование
- Настройте **Worker Mode** для n8n
- Используйте **Docker** для изоляции процессов

## Готовый Workflow

После настройки всех нод, ваш workflow будет выглядеть так:

```
Webhook → Transcribe Audio → Summarize Text → Format Result → Save to Sheets → Response
```

Этот workflow автоматически:
1. ✅ Принимает аудио файлы
2. ✅ Транскрибирует их через ваш сервис
3. ✅ Создает краткое резюме
4. ✅ Сохраняет результаты в Google Sheets
5. ✅ Возвращает структурированный ответ

**Готово к использованию!** 🚀

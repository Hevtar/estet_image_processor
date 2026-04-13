# Vision API Service

Real-time API для подбора продуктов ESTET по изображениям клиента.

## Функционал

- Прием изображений от клиента (через n8n)
- AI-анализ через Gemini
- Векторный поиск по PGVector
- Multi-factor ранжирование
- Интеграция с n8n

## Запуск

### Локально

```bash
# Установка зависимостей
pip install -r requirements.txt
pip install -e ../../packages/estet-shared

# Запуск сервера
uvicorn app.main:app --reload --port 8000

# Swagger UI
# http://localhost:8000/docs
```

### Docker

```bash
docker build -t estet-vision-api .
docker run --env-file .env -p 8000:8000 estet-vision-api
```

## API Endpoints

### POST /api/v1/search
Поиск по изображению.

```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "X-API-Key: your_api_key" \
  -F "file=@photo.jpg"
```

### POST /api/v1/search/text
Поиск по текстовому описанию.

```bash
curl -X POST http://localhost:8000/api/v1/search/text \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{"query": "Светлая дверь в современном стиле"}'
```

### GET /api/v1/products/{id}
Получить продукт по ID.

### GET /health
Health check.

## Интеграция с n8n

1. HTTP Request node → `POST /api/v1/search`
2. Прикрепите изображение из Telegram
3. Получите список похожих продуктов
4. Отформатируйте и отправьте в Telegram

## Тестирование

```bash
pytest
```

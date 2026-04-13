# 📡 API Спецификация

## Vision API

Base URL: `https://your-domain.com/api/v1`

### Аутентификация

Все endpoints требуют API ключ в заголовке:

```
X-API-Key: your_api_key_here
```

### Endpoints

---

#### POST /search

Поиск похожих продуктов по изображению.

**Request:**
- Content-Type: `multipart/form-data`
- Parameters:
  - `file` (image): Изображение (JPEG, PNG, WebP, макс. 10MB)
  - `max_results` (int, optional): Максимум результатов (по умолчанию: 10)
  - `category` (string, optional): Фильтр по категории
  - `style` (string, optional): Фильтр по стилю

**Response 200:**
```json
{
  "success": true,
  "results": [
    {
      "id": "uuid",
      "name": "Дверь Межкомнатная ESTET Classic",
      "category": "Двери межкомнатные",
      "style": "неоклассика",
      "color_family": "белый",
      "ai_semantic_description": "Элегантная межкомнатная дверь...",
      "main_image_url": "https://...",
      "product_url": "https://...",
      "score": 0.95
    }
  ],
  "total": 10,
  "analysis": {
    "style": "современный",
    "colors": ["серый", "белый"],
    "description": "Современный интерьер в светлых тонах..."
  }
}
```

**Example:**
```bash
curl -X POST https://your-domain.com/api/v1/search \
  -H "X-API-Key: your_key" \
  -F "file=@room-photo.jpg" \
  -F "max_results=5"
```

---

#### POST /search/text

Поиск продуктов по текстовому описанию.

**Request:**
- Content-Type: `application/json`
- Body:
```json
{
  "query": "Светлая дверь в современном стиле",
  "max_results": 10,
  "category": "Двери межкомнатные",
  "style": "современный"
}
```

**Response 200:**
```json
{
  "success": true,
  "results": [...],
  "total": 5
}
```

**Example:**
```bash
curl -X POST https://your-domain.com/api/v1/search/text \
  -H "X-API-Key: your_key" \
  -H "Content-Type: application/json" \
  -d '{"query": "Белая дверь в стиле минимализм"}'
```

---

#### GET /products/{product_id}

Получить информацию о продукте.

**Response 200:**
```json
{
  "id": "uuid",
  "name": "Дверь ESTET Modern",
  "category": "Двери межкомнатные",
  "style": "современный",
  "color_family": "серый",
  "ai_semantic_description": "...",
  "main_image_url": "https://...",
  "product_url": "https://...",
  "score": 1.0
}
```

---

#### GET /health

Health check endpoint (без аутентификации).

**Response 200:**
```json
{
  "status": "healthy",
  "service": "vision-api"
}
```

---

## Parser API

Base URL: `http://localhost:8001/api/v1`

### Endpoints

---

#### POST /parse

Запустить парсинг.

**Request:**
```json
{
  "full_parse": true,
  "skip_images": false,
  "skip_ai": false
}
```

**Response 200:**
```json
{
  "success": true,
  "message": "Запущен полный парсинг каталога",
  "stats": {}
}
```

---

#### GET /status

Получить статус парсера.

**Response 200:**
```json
{
  "status": "idle",
  "products_parsed": 0,
  "collections_found": 0,
  "images_downloaded": 0,
  "errors": []
}
```

---

#### GET /stats

Получить статистику парсинга.

**Response 200:**
```json
{
  "total_collections": 15,
  "total_products": 342,
  "total_images": 1520,
  "last_parse_date": "2026-04-10T02:00:00"
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Файл должен быть изображением"
}
```

### 403 Forbidden
```json
{
  "detail": "Invalid API key"
}
```

### 404 Not Found
```json
{
  "detail": "Продукт не найден"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Ошибка поиска: ..."
}
```

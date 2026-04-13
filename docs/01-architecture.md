# 🏗️ Архитектура ESTET Platform

## Обзор

ESTET Platform состоит из двух независимых микросервисов:

### 1. Parser Service
**Назначение:** Batch processing для сбора и подготовки каталога продуктов

**Компоненты:**
- **Crawler** — обход сайта moscow.estetdveri.ru через Selenium
- **Scraper** — извлечение данных из HTML (BeautifulSoup)
- **Downloader** — асинхронное скачивание изображений
- **AI Analyzer** — генерация описаний через Gemini
- **Exporter** — сохранение в PostgreSQL + PGVector

**Режим работы:** Cron job (1 раз в неделю)

### 2. Vision API Service
**Назначение:** Real-time API для подбора продуктов по фото

**Компоненты:**
- **FastAPI Endpoints** — прием запросов из n8n
- **Image Analyzer** — анализ фото клиента через Gemini
- **Vector Search** — поиск похожих в PGVector
- **Ranking** — multi-factor ранжирование результатов

**Режим работы:** 24/7 HTTP API

### 3. Shared Package
**Назначение:** Общий код для обоих сервисов

**Компоненты:**
- Pydantic/SQLAlchemy модели
- Gemini API клиент
- Database утилиты
- Валидаторы

## Data Flow

```
┌─────────────────┐
│  ESTET Website  │
└────────┬────────┘
         │ (1) Парсинг
         ↓
┌─────────────────┐
│  Parser Service │
│  - Selenium     │
│  - BeautifulSoup│
│  - Gemini AI    │
└────────┬────────┘
         │ (2) Экспорт
         ↓
┌─────────────────┐
│  PostgreSQL     │
│  + PGVector     │
└────────┬────────┘
         │ (3) Поиск
         ↓
┌─────────────────┐
│  Vision API     │
│  - FastAPI      │
│  - Gemini AI    │
└────────┬────────┘
         │ (4) Ответ
         ↓
┌─────────────────┐
│  n8n Workflow   │
│  → Telegram Bot │
└─────────────────┘
```

## Технологический стек

### Backend
- **Python 3.11+**
- **FastAPI** — веб-фреймворк
- **SQLAlchemy 2.0** — ORM
- **Pydantic V2** — валидация данных

### Парсинг
- **Selenium 4** — браузерная автоматизация
- **BeautifulSoup4** — парсинг HTML
- **aiohttp** — асинхронные HTTP запросы

### AI
- **Gemini 2.0 Flash Lite** (через Polza.ai)
- **PGVector** — векторный поиск

### База данных
- **PostgreSQL 15+**
- **pgvector extension**

### DevOps
- **Docker & Docker Compose**
- **Nginx** — reverse proxy
- **GitHub Actions** — CI/CD

## Безопасность

- API Key аутентификация для Vision API
- Rate limiting на endpoints
- Валидация всех входных данных
- SQL injection защита через ORM
- CORS настройки для n8n интеграции

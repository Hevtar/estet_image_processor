# 📦 ПОЛНАЯ СТРУКТУРА ПРОЕКТА ESTET PLATFORM

**Версия:** 1.0 | **Для исполнителя:** Qwen Code (Vibe Coding)

---

## 🗂️ СТРУКТУРА ФАЙЛОВ И ПАПОК

```
estet-platform/
│
├── README.md                           # Главная документация проекта
├── .gitignore                          # Git ignore правила
├── .env.example                        # Пример конфигурации
├── docker-compose.yml                  # Локальная разработка
├── Makefile                            # Команды для разработки
│
├── docs/                               # 📚 Документация
│   ├── 01-architecture.md              # Архитектура системы
│   ├── 02-database-schema.md           # Схема БД
│   ├── 03-api-specification.md         # API спецификация
│   ├── 04-deployment-guide.md          # Деплой в production
│   ├── 05-development-guide.md         # Гайд для разработчиков
│   └── 06-qwen-implementation-plan.md  # План реализации для Qwen Code
│
├── packages/                           # 📦 Общие пакеты
│   └── estet-shared/
│       ├── estet_shared/
│       │   ├── __init__.py
│       │   ├── models/                 # Pydantic/SQLAlchemy модели
│       │   │   ├── __init__.py
│       │   │   ├── product.py
│       │   │   ├── collection.py
│       │   │   └── embedding.py
│       │   ├── database/               # Database утилиты
│       │   │   ├── __init__.py
│       │   │   ├── connection.py
│       │   │   └── migrations/
│       │   ├── ai_clients/             # AI клиенты
│       │   │   ├── __init__.py
│       │   │   ├── gemini_client.py
│       │   │   └── embedding_generator.py
│       │   └── utils/                  # Общие утилиты
│       │       ├── __init__.py
│       │       ├── image_processing.py
│       │       └── validators.py
│       ├── tests/
│       │   ├── test_models.py
│       │   └── test_ai_clients.py
│       ├── pyproject.toml
│       ├── setup.py
│       └── README.md
│
├── services/                           # 🚀 Микросервисы
│   │
│   ├── parser/                         # Сервис парсинга
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py                 # FastAPI app (управление)
│   │   │   ├── config.py               # Настройки
│   │   │   │
│   │   │   ├── parser/                 # Парсинг сайта
│   │   │   │   ├── __init__.py
│   │   │   │   ├── crawler.py
│   │   │   │   ├── scraper.py
│   │   │   │   └── url_discovery.py
│   │   │   │
│   │   │   ├── downloader/             # Скачивание изображений
│   │   │   │   ├── __init__.py
│   │   │   │   ├── image_downloader.py
│   │   │   │   └── storage.py
│   │   │   │
│   │   │   ├── analyzer/               # AI анализ
│   │   │   │   ├── __init__.py
│   │   │   │   ├── description_generator.py
│   │   │   │   └── embedding_generator.py
│   │   │   │
│   │   │   ├── pipeline/               # Data pipeline
│   │   │   │   ├── __init__.py
│   │   │   │   ├── validator.py
│   │   │   │   ├── deduplicator.py
│   │   │   │   └── exporter.py
│   │   │   │
│   │   │   └── api/                    # API endpoints
│   │   │       ├── __init__.py
│   │   │       ├── routes.py
│   │   │       └── dependencies.py
│   │   │
│   │   ├── scripts/
│   │   │   ├── run_parser.py           # Главный скрипт парсинга
│   │   │   ├── export_to_db.py         # Экспорт в PostgreSQL
│   │   │   ├── validate_data.py        # Валидация данных
│   │   │   └── test_selectors.py       # Тестирование CSS селекторов
│   │   │
│   │   ├── data/                       # Локальное хранилище
│   │   │   ├── images/
│   │   │   │   ├── collections/
│   │   │   │   └── products/
│   │   │   ├── raw/                    # HTML страницы
│   │   │   └── processed/              # JSON результаты
│   │   │
│   │   ├── tests/
│   │   │   ├── test_crawler.py
│   │   │   ├── test_scraper.py
│   │   │   ├── test_downloader.py
│   │   │   └── test_analyzer.py
│   │   │
│   │   ├── logs/                       # Логи парсинга
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── .env.example
│   │   └── README.md
│   │
│   └── vision-api/                     # Сервис Vision API
│       ├── app/
│       │   ├── __init__.py
│       │   ├── main.py                 # FastAPI app
│       │   ├── config.py
│       │   │
│       │   ├── api/                    # API endpoints
│       │   │   ├── __init__.py
│       │   │   ├── routes.py
│       │   │   ├── dependencies.py
│       │   │   └── middleware.py
│       │   │
│       │   ├── services/               # Business logic
│       │   │   ├── __init__.py
│       │   │   ├── image_analyzer.py
│       │   │   ├── vector_search.py
│       │   │   └── ranking.py
│       │   │
│       │   └── schemas/                # Request/Response модели
│       │       ├── __init__.py
│       │       ├── request.py
│       │       └── response.py
│       │
│       ├── tests/
│       │   ├── test_api.py
│       │   ├── test_image_analyzer.py
│       │   ├── test_vector_search.py
│       │   ├── test_n8n_integration.py
│       │   └── fixtures/
│       │       └── test_images/
│       │
│       ├── Dockerfile
│       ├── requirements.txt
│       ├── .env.example
│       └── README.md
│
├── infrastructure/                     # 🏗️ Инфраструктура
│   ├── docker-compose.yml              # Локальная разработка
│   ├── docker-compose.prod.yml         # Production compose
│   ├── postgres/
│   │   └── init.sql                    # Начальная схема БД
│   ├── nginx/
│   │   └── nginx.conf                  # Nginx конфиг (если нужен)
│   └── railway/
│       ├── parser-railway.toml
│       └── api-railway.toml
│
├── .github/                            # 🔄 CI/CD
│   └── workflows/
│       ├── parser-ci.yml               # CI для парсера
│       ├── api-ci.yml                  # CI для API
│       └── deploy.yml                  # Деплой
│
└── scripts/                            # 🛠️ Вспомогательные скрипты
    ├── setup-dev.sh                    # Настройка dev окружения
    ├── create-migration.sh             # Создание миграции БД
    └── health-check.sh                 # Проверка здоровья сервисов
```

---

## 📄 СОДЕРЖИМОЕ КЛЮЧЕВЫХ ФАЙЛОВ

### 1. `README.md` (корень проекта)

```markdown
# 🎨 ESTET Platform

Платформа для автоматического подбора продуктов фабрики ESTET по изображениям.

## 🏗️ Архитектура

- **Parser Service** — парсинг каталога, генерация AI-описаний
- **Vision API** — real-time поиск продуктов по фото клиента
- **Shared Package** — общие модели и утилиты

## 🚀 Быстрый старт

### Требования
- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 15+ с расширением PGVector
- ChromeDriver (для парсера)

### Установка

```bash
# 1. Клонировать репозиторий
git clone https://github.com/your-org/estet-platform.git
cd estet-platform

# 2. Установить зависимости
make install

# 3. Настроить переменные окружения
cp .env.example .env
# Заполнить POLZA_API_KEY и другие

# 4. Запустить БД
docker-compose up -d postgres

# 5. Запустить парсер (первый запуск)
cd services/parser
python scripts/run_parser.py

# 6. Запустить Vision API
cd services/vision-api
uvicorn app.main:app --reload
```

## 📚 Документация

- [Архитектура](docs/01-architecture.md)
- [API Спецификация](docs/03-api-specification.md)
- [Deployment Guide](docs/04-deployment-guide.md)
- [Development Guide](docs/05-development-guide.md)

## 🧪 Тестирование

```bash
# Все тесты
make test

# Только parser
make test-parser

# Только API
make test-api
```

## 📦 Сервисы

### Parser Service
- Порт: 8001 (API управления)
- Запуск: `cd services/parser && python scripts/run_parser.py`
- Документация: [services/parser/README.md](services/parser/README.md)

### Vision API
- Порт: 8000
- Swagger: http://localhost:8000/docs
- Документация: [services/vision-api/README.md](services/vision-api/README.md)

## 🤝 Contributing

См. [CONTRIBUTING.md](CONTRIBUTING.md)

## 📄 License

MIT License
```

---

### 2. `.env.example` (корень проекта)

```env
# ========================================
# ESTET PLATFORM - Environment Variables
# ========================================

# ----- Shared Configuration -----
ENVIRONMENT=development  # development | staging | production

# PostgreSQL Database
DATABASE_URL=postgresql+asyncpg://estet:estet_dev_password@localhost:5432/estet_platform
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# Polza.ai (Gemini API)
POLZA_API_KEY=your_polza_api_key_here
POLZA_API_URL=https://api.polza.ai/v1
GEMINI_MODEL=google/gemini-2.0-flash-lite
GEMINI_MODEL_FALLBACK=google/gemini-2.0-flash
GEMINI_MAX_TOKENS=2048
GEMINI_TEMPERATURE=0.2

# Logging
LOG_LEVEL=INFO  # DEBUG | INFO | WARNING | ERROR
LOG_FORMAT=json  # json | text

# ----- Parser Service -----
PARSER_API_PORT=8001
PARSER_HEADLESS_BROWSER=true
PARSER_SCRAPING_DELAY=2  # секунды между запросами
PARSER_MAX_RETRIES=3
PARSER_TIMEOUT=30
PARSER_IMAGES_PATH=services/parser/data/images
PARSER_JSON_OUTPUT_PATH=services/parser/data/processed

# ----- Vision API Service -----
VISION_API_PORT=8000
VISION_API_KEY=your_secret_api_key_for_n8n
VISION_MAX_IMAGE_SIZE_MB=10
VISION_MAX_RESULTS=10
VISION_AUTH_REQUIRED=true
VISION_ALLOWED_ORIGINS=http://localhost:3000,https://your-n8n-instance.app

# Image Processing
IMAGE_DETAIL_LEVEL=high  # low | auto | high

# ----- Monitoring (Optional) -----
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
SENTRY_ENVIRONMENT=development
SENTRY_TRACES_SAMPLE_RATE=0.1
```

---

### 3. `Makefile` (корень проекта)

```makefile
.PHONY: help install test clean dev

help:
	@echo "🎨 ESTET Platform - Available Commands:"
	@echo ""
	@echo "  make install        - Установить все зависимости"
	@echo "  make dev            - Запустить в dev режиме"
	@echo "  make test           - Запустить все тесты"
	@echo "  make test-parser    - Тесты парсера"
	@echo "  make test-api       - Тесты Vision API"
	@echo "  make lint           - Проверка кода (black, flake8)"
	@echo "  make format         - Форматирование кода"
	@echo "  make clean          - Очистка временных файлов"
	@echo "  make docker-up      - Запуск PostgreSQL в Docker"
	@echo "  make docker-down    - Остановка Docker контейнеров"
	@echo "  make migrate        - Применить миграции БД"
	@echo ""

install:
	@echo "📦 Установка зависимостей..."
	cd packages/estet-shared && pip install -e .
	cd services/parser && pip install -r requirements.txt
	cd services/vision-api && pip install -r requirements.txt
	@echo "✅ Зависимости установлены"

dev:
	@echo "🚀 Запуск в dev режиме..."
	docker-compose up -d postgres
	@echo "✅ PostgreSQL запущен"
	@echo "Запустите сервисы вручную:"
	@echo "  Parser:  cd services/parser && python scripts/run_parser.py"
	@echo "  API:     cd services/vision-api && uvicorn app.main:app --reload"

test:
	@echo "🧪 Запуск всех тестов..."
	cd packages/estet-shared && pytest
	cd services/parser && pytest
	cd services/vision-api && pytest

test-parser:
	@echo "🧪 Тесты парсера..."
	cd services/parser && pytest -v

test-api:
	@echo "🧪 Тесты Vision API..."
	cd services/vision-api && pytest -v

lint:
	@echo "🔍 Проверка кода..."
	flake8 packages/ services/ --max-line-length=120
	black --check packages/ services/

format:
	@echo "✨ Форматирование кода..."
	black packages/ services/
	isort packages/ services/

clean:
	@echo "🧹 Очистка временных файлов..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

migrate:
	@echo "🗄️ Применение миграций..."
	cd packages/estet-shared && alembic upgrade head
```

---

### 4. `docker-compose.yml` (корень проекта)

```yaml
version: '3.9'

services:
  postgres:
    image: pgvector/pgvector:pg15
    container_name: estet_postgres
    environment:
      POSTGRES_USER: estet
      POSTGRES_PASSWORD: estet_dev_password
      POSTGRES_DB: estet_platform
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./infrastructure/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U estet"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Parser (опционально, для dev можно запускать вручную)
  # parser:
  #   build:
  #     context: ./services/parser
  #     dockerfile: Dockerfile
  #   container_name: estet_parser
  #   env_file:
  #     - .env
  #   volumes:
  #     - ./services/parser/data:/app/data
  #     - ./services/parser/logs:/app/logs
  #   depends_on:
  #     - postgres

  # Vision API (опционально, для dev можно запускать вручную)
  # vision-api:
  #   build:
  #     context: ./services/vision-api
  #     dockerfile: Dockerfile
  #   container_name: estet_vision_api
  #   env_file:
  #     - .env
  #   ports:
  #     - "8000:8000"
  #   depends_on:
  #     - postgres

volumes:
  postgres_data:
```

---

### 5. `.gitignore`

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Environment
.env
.env.local
.env.*.local

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Logs
logs/
*.log

# Data
services/parser/data/images/
services/parser/data/raw/
services/parser/data/processed/
*.jpg
*.jpeg
*.png
*.webp

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/

# Database
*.db
*.sqlite

# OS
.DS_Store
Thumbs.db
```

---

## 📚 ДОКУМЕНТАЦИЯ

### `docs/01-architecture.md`

```markdown
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
- **Railway** — хостинг
- **GitHub Actions** — CI/CD

## Безопасность

- API Key аутентификация для Vision API
- Rate limiting на endpoints
- Валидация всех входных данных
- SQL injection защита через ORM
- CORS настройки для n8n интеграции
```

---

### `docs/02-database-schema.md`

```markdown
# 🗄️ Database Schema

## Таблицы

### 1. `collections`

Коллекции продуктов ESTET.

```sql
CREATE TABLE collections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    slug VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    url VARCHAR(500),
    image_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_collections_slug ON collections(slug);
```

### 2. `products`

Каталог продуктов.

```sql
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    collection_id UUID REFERENCES collections(id) ON DELETE SET NULL,
    
    -- Основные данные
    name VARCHAR(500) NOT NULL,
    slug VARCHAR(500) NOT NULL UNIQUE,
    category VARCHAR(100) NOT NULL, -- 'Двери межкомнатные' | 'Стеновые панели' | 'Порталы каминные'
    
    -- Описания
    original_description TEXT,
    ai_semantic_description TEXT,
    
    -- Характеристики
    style VARCHAR(100),              -- 'неоклассика' | 'современный' | 'минимализм'
    color_family VARCHAR(50),        -- 'белый' | 'серый' | 'коричневый'
    material VARCHAR(255),
    finish_type VARCHAR(100),        -- 'матовый' | 'глянец'
    special_features TEXT[],
    
    -- URLs
    product_url VARCHAR(500) NOT NULL,
    main_image_url VARCHAR(500),
    
    -- Мета-данные
    price DECIMAL(10, 2),
    available_sizes TEXT[],
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_scraped_at TIMESTAMP
);

CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_collection ON products(collection_id);
CREATE INDEX idx_products_style ON products(style);
CREATE INDEX idx_products_color ON products(color_family);
```

### 3. `product_images`

Изображения продуктов.

```sql
CREATE TABLE product_images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID REFERENCES products(id) ON DELETE CASCADE,
    
    original_url VARCHAR(500) NOT NULL,
    local_path VARCHAR(500),
    image_hash VARCHAR(64),
    
    is_primary BOOLEAN DEFAULT false,
    display_order INTEGER DEFAULT 0,
    
    width INTEGER,
    height INTEGER,
    size_bytes INTEGER,
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_product_images_product ON product_images(product_id);
CREATE INDEX idx_product_images_primary ON product_images(product_id, is_primary);
```

### 4. `product_embeddings`

Векторные представления для поиска.

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE product_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID REFERENCES products(id) ON DELETE CASCADE,
    
    -- Векторное представление (768 dimensions для Gemini)
    embedding vector(768) NOT NULL,
    
    -- Тип embedding
    embedding_type VARCHAR(50) DEFAULT 'semantic',  -- 'semantic' | 'visual'
    
    -- Мета-данные
    model_version VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Индекс для быстрого векторного поиска
CREATE INDEX idx_product_embeddings_vector ON product_embeddings 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX idx_product_embeddings_product ON product_embeddings(product_id);
```

### 5. `parsing_logs`

Логи парсинга для мониторинга.

```sql
CREATE TABLE parsing_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    started_at TIMESTAMP NOT NULL,
    finished_at TIMESTAMP,
    status VARCHAR(50),  -- 'running' | 'completed' | 'failed'
    
    products_found INTEGER DEFAULT 0,
    products_processed INTEGER DEFAULT 0,
    products_failed INTEGER DEFAULT 0,
    
    error_message TEXT,
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_parsing_logs_status ON parsing_logs(status);
CREATE INDEX idx_parsing_logs_started ON parsing_logs(started_at DESC);
```

## Индексы для производительности

```sql
-- Full-text search по названию и описанию
CREATE INDEX idx_products_fts ON products 
USING gin(to_tsvector('russian', name || ' ' || COALESCE(ai_semantic_description, '')));

-- Composite индексы для частых запросов
CREATE INDEX idx_products_category_style ON products(category, style);
CREATE INDEX idx_products_collection_category ON products(collection_id, category);
```

## Начальные данные

```sql
-- Категории (enum через constraint)
ALTER TABLE products ADD CONSTRAINT valid_category 
CHECK (category IN ('Двери межкомнатные', 'Стеновые панели', 'Порталы каминные', 'Другое'));

-- Стили
ALTER TABLE products ADD CONSTRAINT valid_style 
CHECK (style IN ('классика', 'неоклассика', 'современный', 'минимализм', 'лофт', 'скандинавский', 'арт-деко', 'unknown'));
```
```

---

### `docs/06-qwen-implementation-plan.md`

```markdown
# 🚀 ПЛАН РЕАЛИЗАЦИИ ДЛЯ QWEN CODE

**Исполнитель:** Qwen Code (Vibe Coding)  
**Цель:** Пошаговая реализация ESTET Platform

---

## 📋 ОБЩИЙ ПЛАН

### ✅ PHASE 0: ПОДГОТОВКА (1-2 часа)
### ✅ PHASE 1: SHARED PACKAGE (4-6 часов)
### 🔄 PHASE 2: PARSER SERVICE (16-20 часов)
### 🔄 PHASE 3: VISION API SERVICE (12-16 часов)
### 🔄 PHASE 4: INTEGRATION & TESTING (6-8 часов)
### 🔄 PHASE 5: DEPLOYMENT (4-6 часов)

---

## PHASE 0: ПОДГОТОВКА ОКРУЖЕНИЯ

### Задачи:

#### 0.1 Создать структуру проекта
```bash
mkdir -p estet-platform/{docs,packages/estet-shared,services/{parser,vision-api},infrastructure,scripts}
cd estet-platform
```

#### 0.2 Инициализировать Git
```bash
git init
# Создать .gitignore (см. выше)
git add .
git commit -m "Initial project structure"
```

#### 0.3 Настроить виртуальное окружение
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows
```

#### 0.4 Создать .env файл
```bash
cp .env.example .env
# Заполнить POLZA_API_KEY и другие переменные
```

#### 0.5 Запустить PostgreSQL
```bash
docker-compose up -d postgres
```

#### ✅ Критерии завершения:
- [ ] Структура папок создана
- [ ] Git репозиторий инициализирован
- [ ] PostgreSQL запущен и доступен
- [ ] .env файл настроен

---

## PHASE 1: SHARED PACKAGE

### Цель: Создать общий пакет с моделями и утилитами

### Задачи:

#### 1.1 Создать базовую структуру пакета

**Файл:** `packages/estet-shared/pyproject.toml`
```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "estet-shared"
version = "0.1.0"
description = "Shared models and utilities for ESTET Platform"
requires-python = ">=3.11"
dependencies = [
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "sqlalchemy[asyncio]>=2.0.23",
    "asyncpg>=0.29.0",
    "pgvector>=0.2.4",
    "httpx>=0.25.2",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.0.0",
    "flake8>=6.0.0",
]
```

**Файл:** `packages/estet-shared/setup.py`
```python
from setuptools import setup, find_packages

setup(
    name="estet-shared",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pydantic>=2.5.0",
        "sqlalchemy[asyncio]>=2.0.23",
        "asyncpg>=0.29.0",
    ],
)
```

#### 1.2 Создать модели данных

**Файл:** `packages/estet-shared/estet_shared/models/product.py`
```python
"""
SQLAlchemy и Pydantic модели для продуктов.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy import Column, String, Text, DECIMAL, ARRAY, DateTime, Boolean, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from .base import Base


# ========================================
# SQLAlchemy ORM Models
# ========================================

class Collection(Base):
    """Коллекция продуктов"""
    __tablename__ = "collections"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False, unique=True)
    slug = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    url = Column(String(500))
    image_url = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    products = relationship("Product", back_populates="collection")


class Product(Base):
    """Продукт в каталоге"""
    __tablename__ = "products"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    collection_id = Column(PGUUID(as_uuid=True), ForeignKey("collections.id", ondelete="SET NULL"))

    # Основные данные
    name = Column(String(500), nullable=False)
    slug = Column(String(500), nullable=False, unique=True)
    category = Column(String(100), nullable=False)

    # Описания
    original_description = Column(Text)
    ai_semantic_description = Column(Text)

    # Характеристики
    style = Column(String(100))
    color_family = Column(String(50))
    material = Column(String(255))
    finish_type = Column(String(100))
    special_features = Column(ARRAY(Text))

    # URLs
    product_url = Column(String(500), nullable=False)
    main_image_url = Column(String(500))

    # Мета-данные
    price = Column(DECIMAL(10, 2))
    available_sizes = Column(ARRAY(Text))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_scraped_at = Column(DateTime)

    # Relationships
    collection = relationship("Collection", back_populates="products")
    images = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")
    embeddings = relationship("ProductEmbedding", back_populates="product", cascade="all, delete-orphan")


class ProductImage(Base):
    """Изображение продукта"""
    __tablename__ = "product_images"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    product_id = Column(PGUUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"))

    original_url = Column(String(500), nullable=False)
    local_path = Column(String(500))
    image_hash = Column(String(64))

    is_primary = Column(Boolean, default=False)
    display_order = Column(Integer, default=0)

    width = Column(Integer)
    height = Column(Integer)
    size_bytes = Column(Integer)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    product = relationship("Product", back_populates="images")


# ========================================
# Pydantic Schemas
# ========================================

class ProductBase(BaseModel):
    """Базовая схема продукта"""
    name: str
    category: str
    style: Optional[str] = None
    color_family: Optional[str] = None
    material: Optional[str] = None
    product_url: HttpUrl


class ProductCreate(ProductBase):
    """Схема для создания продукта"""
    collection_id: Optional[UUID] = None
    slug: str
    original_description: Optional[str] = None
    ai_semantic_description: Optional[str] = None
    finish_type: Optional[str] = None
    special_features: List[str] = Field(default_factory=list)
    main_image_url: Optional[HttpUrl] = None
    price: Optional[float] = None
    available_sizes: List[str] = Field(default_factory=list)


class ProductResponse(ProductBase):
    """Схема ответа с продуктом"""
    id: UUID
    collection_id: Optional[UUID]
    slug: str
    ai_semantic_description: Optional[str]
    main_image_url: Optional[HttpUrl]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

**Файл:** `packages/estet-shared/estet_shared/models/base.py`
```python
"""
Базовая модель SQLAlchemy.
"""
from sqlalchemy.orm import declarative_base

Base = declarative_base()
```

**Файл:** `packages/estet-shared/estet_shared/models/__init__.py`
```python
"""
Модели данных для ESTET Platform.
"""
from .base import Base
from .product import Collection, Product, ProductImage, ProductCreate, ProductResponse
from .embedding import ProductEmbedding, EmbeddingCreate

__all__ = [
    "Base",
    "Collection",
    "Product",
    "ProductImage",
    "ProductCreate",
    "ProductResponse",
    "ProductEmbedding",
    "EmbeddingCreate",
]
```

#### 1.3 Создать модель Embedding

**Файл:** `packages/estet-shared/estet_shared/models/embedding.py`
```python
"""
Модели для векторных представлений.
"""
from datetime import datetime
from typing import List
from uuid import UUID, uuid4

from pydantic import BaseModel
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from .base import Base


class ProductEmbedding(Base):
    """Векторное представление продукта"""
    __tablename__ = "product_embeddings"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    product_id = Column(PGUUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"))

    # Вектор (768 dimensions для Gemini embeddings)
    embedding = Column(Vector(768), nullable=False)

    embedding_type = Column(String(50), default="semantic")
    model_version = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    product = relationship("Product", back_populates="embeddings")


class EmbeddingCreate(BaseModel):
    """Схема для создания embedding"""
    product_id: UUID
    embedding: List[float]
    embedding_type: str = "semantic"
    model_version: str = "gemini-2.0-flash-lite"
```

#### 1.4 Создать Database утилиты

**Файл:** `packages/estet-shared/estet_shared/database/connection.py`
```python
"""
Database connection и session management.
"""
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

logger = logging.getLogger(__name__)


class Database:
    """Database connection manager"""

    def __init__(self, database_url: str, echo: bool = False):
        self.engine = create_async_engine(
            database_url,
            echo=echo,
            poolclass=NullPool,  # Для async лучше без пула
        )
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Context manager для сессии"""
        async with self.async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Database error: {e}")
                raise

    async def close(self):
        """Закрыть соединение"""
        await self.engine.dispose()

    async def create_tables(self):
        """Создать все таблицы"""
        from estet_shared.models import Base
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            logger.info("✅ Database tables created")

    async def drop_tables(self):
        """Удалить все таблицы (ОСТОРОЖНО!)"""
        from estet_shared.models import Base
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            logger.warning("⚠️ Database tables dropped")
```

#### 1.5 Создать Gemini клиент

**Файл:** `packages/estet-shared/estet_shared/ai_clients/gemini_client.py`
```python
"""
Клиент для Gemini API через Polza.ai.
"""
import asyncio
import base64
import json
import logging
from typing import Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class GeminiClient:
    """Клиент для работы с Gemini через Polza.ai"""

    def __init__(
        self,
        api_key: str,
        api_url: str = "https://api.polza.ai/v1",
        model: str = "google/gemini-2.0-flash-lite",
        max_retries: int = 3,
    ):
        self.api_key = api_key
        self.api_url = api_url
        self.model = model
        self.max_retries = max_retries

    async def analyze_image(
        self,
        image_bytes: bytes,
        prompt: str,
        mime_type: str = "image/jpeg",
        max_tokens: int = 2048,
        temperature: float = 0.2,
    ) -> Dict:
        """
        Анализирует изображение с помощью Gemini.

        Args:
            image_bytes: Байты изображения
            prompt: Текстовый промпт
            mime_type: MIME тип изображения
            max_tokens: Максимум токенов в ответе
            temperature: Температура генерации

        Returns:
            Dict с результатом анализа
        """
        # Конвертируем в base64
        base64_image = base64.b64encode(image_bytes).decode("utf-8")
        data_uri = f"data:{mime_type};base64,{base64_image}"

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": data_uri, "detail": "high"}
                        }
                    ]
                }
            ],
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        return await self._call_api_with_retry(payload)

    async def generate_text(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> Dict:
        """
        Генерирует текст без изображения.

        Args:
            prompt: Текстовый промпт
            max_tokens: Максимум токенов
            temperature: Температура

        Returns:
            Dict с результатом
        """
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        return await self._call_api_with_retry(payload)

    async def generate_embedding(
        self,
        text: str
    ) -> List[float]:
        """
        Генерирует embedding для текста.

        Note: Polza.ai может не поддерживать embeddings endpoint.
        В таком случае используем обходной путь через chat completion.

        Args:
            text: Текст для embedding

        Returns:
            List[float]: Вектор embedding
        """
        # TODO: Проверить поддержку embeddings API в Polza
        # Временное решение: генерируем через анализ
        logger.warning("Embeddings через Gemini API не реализованы, используем заглушку")
        return [0.0] * 768  # Заглушка

    async def _call_api_with_retry(self, payload: Dict) -> Dict:
        """Вызов API с retry логикой"""
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        f"{self.api_url}/chat/completions",
                        json=payload,
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json"
                        }
                    )
                    response.raise_for_status()
                    data = response.json()

                    # Извлекаем контент
                    content = data["choices"][0]["message"]["content"]

                    # Пытаемся распарсить как JSON (если промпт требовал JSON)
                    try:
                        cleaned = content.strip()
                        if cleaned.startswith("```"):
                            lines = cleaned.split("\n")
                            cleaned = "\n".join(lines[1:-1])
                        return json.loads(cleaned)
                    except json.JSONDecodeError:
                        # Если не JSON, возвращаем как есть
                        return {"content": content}

            except httpx.TimeoutException:
                logger.warning(f"⏱️ Timeout на попытке {attempt + 1}/{self.max_retries}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise

            except Exception as e:
                logger.error(f"❌ Ошибка API на попытке {attempt + 1}: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise

        raise Exception("Max retries exceeded")
```

#### ✅ Критерии завершения Phase 1:
- [ ] Пакет estet-shared установлен (`pip install -e packages/estet-shared`)
- [ ] Модели Product, Collection, Embedding созданы
- [ ] Database утилиты работают
- [ ] GeminiClient тестируется успешно
- [ ] Тесты проходят: `cd packages/estet-shared && pytest`

---

## PHASE 2: PARSER SERVICE

*(Подробный план для Parser Service — около 30-40 файлов)*

**Основные модули:**
1. Crawler (Selenium)
2. Scraper (BeautifulSoup)
3. Image Downloader
4. AI Analyzer
5. Pipeline & Exporter

**Детальная инструкция будет в отдельном документе для Qwen Code после завершения Phase 1.**

---

## PHASE 3: VISION API SERVICE

*(Подробный план для Vision API — около 20-25 файлов)*

**Основные модули:**
1. FastAPI endpoints
2. Image Analyzer
3. Vector Search
4. Ranking
5. n8n Integration

---

## ✅ ИТОГОВЫЙ CHECKLIST

```yaml
Phase 0: Подготовка
  ✅ Структура проекта создана
  ✅ Git инициализирован
  ✅ PostgreSQL запущен
  ✅ .env настроен

Phase 1: Shared Package
  ✅ pyproject.toml создан
  ✅ Модели Product, Collection, Embedding
  ✅ Database утилиты
  ✅ GeminiClient
  ✅ Тесты проходят

Phase 2: Parser Service
  ⏳ Crawler реализован
  ⏳ Scraper реализован
  ⏳ Image Downloader реализован
  ⏳ AI Analyzer реализован
  ⏳ Pipeline & Exporter
  ⏳ Скрипт run_parser.py
  ⏳ Тесты проходят

Phase 3: Vision API
  ⏳ FastAPI app
  ⏳ Image Analyzer
  ⏳ Vector Search
  ⏳ Ranking
  ⏳ n8n integration tests
  ⏳ Тесты проходят

Phase 4: Integration
  ⏳ End-to-end тесты
  ⏳ Нагрузочное тестирование
  ⏳ Документация

Phase 5: Deployment
  ⏳ Deploy на Railway
  ⏳ Мониторинг настроен
  ⏳ Production готов
```

---

**Готово! Qwen Code может начинать с Phase 0 и Phase 1.** 🚀
```

---

## 🎯 ИНСТРУКЦИЯ ДЛЯ QWEN CODE

### Как использовать эту документацию:

1. **Читай поэтапно:** Начни с Phase 0, затем Phase 1
2. **Создавай файлы точно по структуре:** Все пути важны
3. **Тестируй после каждого этапа:** Не переходи дальше пока не пройдут тесты
4. **Используй комментарии:** Весь код должен быть задокументирован
5. **Логируй всё:** Используй `logging` для отладки

### Начни с:

```bash
# 1. Создай корневую папку
mkdir estet-platform
cd estet-platform

# 2. Создай базовую структуру (можешь написать скрипт)
mkdir -p docs packages/estet-shared services/{parser,vision-api} infrastructure scripts

# 3. Создай README.md (используй шаблон выше)
# 4. Создай .gitignore
# 5. Создай .env.example
# 6. Создай docker-compose.yml

# 7. Начинай Phase 1: Shared Package
```

---

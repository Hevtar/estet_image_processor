# 👨‍💻 Development Guide

## Локальная разработка

### Требования

- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 15+ (или Docker для БД)
- ChromeDriver (для парсера)

### Быстрый старт

```bash
# 1. Клонировать репозиторий
git clone https://github.com/your-org/estet-platform.git
cd estet-platform

# 2. Создать виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 3. Установить зависимости
make install

# 4. Настроить окружение
cp .env.example .env
# Заполнить POLZA_API_KEY

# 5. Запустить PostgreSQL
docker-compose up -d postgres

# 6. Запустить сервисы
cd services/vision-api
uvicorn app.main:app --reload

# В другом терминале
cd services/parser
python scripts/run_parser.py --help
```

### Структура проекта

```
estet-platform/
├── packages/
│   └── estet-shared/          # Общий пакет
│       ├── estet_shared/
│       │   ├── models/        # SQLAlchemy/Pydantic модели
│       │   ├── database/      # Database utilities
│       │   ├── ai_clients/    # Gemini client
│       │   └── utils/         # Validators, image processing
│       └── tests/
│
├── services/
│   ├── parser/                # Parser Service
│   │   ├── app/
│   │   │   ├── parser/        # Crawler, Scraper
│   │   │   ├── downloader/    # Image downloader
│   │   │   ├── analyzer/      # AI analysis
│   │   │   ├── pipeline/      # Validation, export
│   │   │   └── api/           # FastAPI endpoints
│   │   └── scripts/
│   │
│   └── vision-api/            # Vision API Service
│       ├── app/
│       │   ├── api/           # Endpoints
│       │   ├── services/      # Business logic
│       │   └── schemas/       # Request/Response models
│       └── tests/
│
├── infrastructure/
│   ├── docker-compose.yml     # Local dev
│   ├── docker-compose.prod.yml # Production
│   ├── postgres/init.sql      # DB schema
│   └── nginx/nginx.conf       # Nginx config
│
└── docs/                      # Документация
```

### Тестирование

```bash
# Все тесты
make test

# Только parser
make test-parser

# Только API
make test-api

# С покрытием
cd services/vision-api
pytest --cov=app --cov-report=html
```

### Линтинг и форматирование

```bash
# Проверка
make lint

# Форматирование
make format
```

### Работа с БД

```bash
# Применить миграции
make migrate

# Подключиться к БД
docker exec -it estet_postgres psql -U estet -d estet_platform
```

### Git Workflow

```bash
# Создать ветку для фичи
git checkout -b feature/my-feature

# Коммиты
git commit -m "feat: add new feature"

# Pull request
git push origin feature/my-feature
```

### Conventional Commits

- `feat:` новая функциональность
- `fix:` исправление бага
- `docs:` изменения в документации
- `refactor:` рефакторинг кода
- `test:` добавление тестов
- `chore:` обновления зависимостей

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

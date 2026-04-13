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

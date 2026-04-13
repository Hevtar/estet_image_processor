# Parser Service

Сервис для автоматического парсинга каталога ESTET.

## Функционал

- Обход сайта moscow.estetdveri.ru через Selenium
- Извлечение данных о продуктах и коллекциях
- Скачивание изображений
- AI-анализ и генерация описаний через Gemini
- Экспорт в PostgreSQL + PGVector

## Запуск

### Локально

```bash
# Установка зависимостей
pip install -r requirements.txt
pip install -e ../../packages/estet-shared

# Запуск полного парсинга
python scripts/run_parser.py --full

# Парсинг одной коллекции
python scripts/run_parser.py --collection https://moscow.estetdveri.ru/kategoriya/dveri

# Парсинг одного продукта
python scripts/run_parser.py --product https://moscow.estetdveri.ru/product/door-123

# Без скачивания изображений
python scripts/run_parser.py --full --skip-images

# Без AI анализа
python scripts/run_parser.py --full --skip-ai
```

### Docker

```bash
docker build -t estet-parser .
docker run --env-file .env estet-parser
```

## API

Документация Swagger: http://localhost:8001/docs

## Структура

```
app/
├── parser/          # Crawler, Scraper, URL Discovery
├── downloader/      # Image Downloader, Storage
├── analyzer/        # Description & Embedding generators
├── pipeline/        # Validator, Deduplicator, Exporter
└── api/             # FastAPI endpoints
```

## Тестирование

```bash
pytest
```

# ESTET Platform - Shared Package

Общий пакет с моделями данных и утилитами для всех сервисов ESTET Platform.

## Установка

```bash
pip install -e .
```

## Структура

- `models/` — SQLAlchemy ORM и Pydantic схемы
- `database/` — Database connection utilities
- `ai_clients/` — Gemini API клиент и embedding generator
- `utils/` — Общие утилиты (image processing, validators)

## Тестирование

```bash
pytest
```

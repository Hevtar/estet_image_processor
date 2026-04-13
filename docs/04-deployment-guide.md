# 🚀 Deployment Guide

Полная инструкция по развёртыванию находится в файле [DEPLOY.md](../DEPLOY.md) в корне проекта.

## Quick Start

### Docker Compose (рекомендуется)

```bash
# 1. Клонировать репозиторий
git clone https://github.com/your-org/estet-platform.git
cd estet-platform

# 2. Настроить переменные окружения
cp .env.example .env
nano .env  # Заполнить API ключи и пароли

# 3. Запустить все сервисы
docker compose -f infrastructure/docker-compose.prod.yml up -d

# 4. Проверить
curl http://localhost:8000/health
```

### Bare Metal (без Docker)

См. полную инструкцию: [DEPLOY.md](../DEPLOY.md#деплой-без-docker-ручная-установка)

## Production Checklist

- [ ] PostgreSQL + PGVector установлен
- [ ] .env.production настроен
- [ ] SSL сертификат получен
- [ ] Nginx настроен
- [ ] Бэкапы настроены
- [ ] Мониторинг настроен
- [ ] CI/CD работает

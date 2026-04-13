# 🚀 ПОДРОБНАЯ ИНСТРУКЦИЯ ПО ДЕПЛОЮ ESTET PLATFORM

## 📋 СОДЕРЖАНИЕ

1. [Требования к серверу](#требования-к-серверу)
2. [Подготовка сервера](#подготовка-сервера)
3. [Установка Docker](#установка-docker)
4. [Настройка PostgreSQL + PGVector](#настройка-postgresql--pgvector)
5. [Развёртывание через Docker Compose](#развёртывание-через-docker-compose)
6. [Настройка Nginx + SSL](#настройка-nginx--ssl)
7. [Настройка CI/CD через GitHub Actions](#настройка-cicd-через-github-actions)
8. [Деплой без Docker (ручная установка)](#деплой-без-docker-ручная-установка)
9. [Мониторинг и логирование](#мониторинг-и-логирование)
10. [Бэкапы и восстановление](#бэкапы-и-восстановление)
11. [Troubleshooting](#troubleshooting)

---

## ТРЕБОВАНИЯ К СЕРВЕРУ

### Минимальные требования

- **CPU:** 2 cores
- **RAM:** 4 GB
- **Storage:** 20 GB SSD
- **OS:** Ubuntu 22.04 LTS / Debian 11 / CentOS 8+
- **Network:** Статический IP, открытые порты 80, 443

### Рекомендуемые требования

- **CPU:** 4 cores
- **RAM:** 8 GB
- **Storage:** 50 GB NVMe
- **OS:** Ubuntu 22.04 LTS
- **Network:** Статический IP, доменное имя

### Необходимые порты

| Порт  | Сервис         | Описание                     |
|-------|----------------|------------------------------|
| 22    | SSH            | Удаленный доступ             |
| 80    | HTTP (Nginx)   | Веб-трафик (редирект на 443) |
| 443   | HTTPS (Nginx)  | Защищенный веб-трафик        |
| 5432  | PostgreSQL     | **Не открывать наружу!**     |
| 8000  | Vision API     | **Только для Nginx**         |

---

## ПОДГОТОВКА СЕРВЕРА

### 1. Подключение к серверу

```bash
ssh root@your-server-ip
```

### 2. Обновление системы

```bash
apt update && apt upgrade -y
```

### 3. Создание пользователя для деплоя

```bash
# Создать пользователя
adduser deployer

# Добавить в группу sudo
usermod -aG sudo deployer

# Переключиться на пользователя
su - deployer
```

### 4. Настройка SSH ключей (рекомендуется)

```bash
# На локальной машине
ssh-keygen -t ed25519 -C "deploy@estet-platform"

# Копировать ключ на сервер
ssh-copy-id deployer@your-server-ip

# Отключить вход по паролю (опционально, на сервере)
sudo nano /etc/ssh/sshd_config
# Изменить: PasswordAuthentication no
sudo systemctl restart sshd
```

### 5. Настройка фаервола

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status
```

### 6. Установка необходимых утилит

```bash
sudo apt install -y curl git wget gnupg software-properties-common
```

---

## УСТАНОВКА DOCKER

### 1. Установка Docker Engine

```bash
# Добавить официальный репозиторий Docker
sudo apt install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Установить Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Проверить установку
docker --version
docker compose version
```

### 2. Добавить пользователя в группу docker

```bash
sudo usermod -aG docker $USER
newgrp docker
```

### 3. Проверка работы Docker

```bash
docker run hello-world
```

---

## НАСТРОЙКА POSTGRESQL + PGVECTOR

### Вариант 1: PostgreSQL в Docker (рекомендуется)

Пропустите этот шаг — PostgreSQL запустится автоматически через docker-compose.

### Вариант 2: Установка PostgreSQL на сервер

```bash
# Установить PostgreSQL 15
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo apt update
sudo apt install -y postgresql-15 postgresql-contrib-15

# Установить PGVector
sudo apt install -y postgresql-15-pgvector

# Проверить установку
sudo -u postgres psql -c "SELECT extname FROM pg_extension;"
```

### Настройка PostgreSQL

```bash
# Подключиться к PostgreSQL
sudo -u postgres psql

# Создать пользователя и базу данных
CREATE USER estet WITH PASSWORD 'your_secure_password_here';
CREATE DATABASE estet_platform OWNER estet;
\c estet_platform
CREATE EXTENSION IF NOT EXISTS vector;

# Предоставить права
GRANT ALL PRIVILEGES ON DATABASE estet_platform TO estet;
ALTER USER estet CREATEDB;

# Проверить расширение
\dx

# Выйти
\q
```

### Инициализация схемы БД

```bash
# Скопировать init.sql на сервер
scp infrastructure/postgres/init.sql deployer@your-server-ip:/tmp/init.sql

# Применить схему
sudo -u postgres psql -d estet_platform -f /tmp/init.sql
```

---

## РАЗВЁРТЫВАНИЕ ЧЕРЕЗ DOCKER COMPOSE

### 1. Клонировать репозиторий

```bash
cd /opt
sudo mkdir -p estet-platform
sudo chown deployer:deployer estet-platform
cd estet-platform

git clone https://github.com/your-org/estet-platform.git .
# Или скопируйте файлы через scp
```

### 2. Создать .env файл для production

```bash
nano .env.production
```

**Содержимое `.env.production`:**

```env
# ========================================
# ESTET PLATFORM - Production Environment
# ========================================

ENVIRONMENT=production

# PostgreSQL
DATABASE_URL=postgresql+asyncpg://estet:YOUR_SECURE_PASSWORD@postgres:5432/estet_platform

# Polza.ai (Gemini API)
POLZA_API_KEY=your_real_polza_api_key_here
POLZA_API_URL=https://api.polza.ai/v1
GEMINI_MODEL=google/gemini-2.0-flash-lite
GEMINI_MODEL_FALLBACK=google/gemini-2.0-flash
GEMINI_MAX_TOKENS=2048
GEMINI_TEMPERATURE=0.2

# Vision API
VISION_API_KEY=generate_a_strong_api_key_here_for_n8n
VISION_MAX_IMAGE_SIZE_MB=10
VISION_MAX_RESULTS=10
VISION_AUTH_REQUIRED=true
VISION_ALLOWED_ORIGINS=https://your-n8n-instance.app

# Parser
PARSER_HEADLESS_BROWSER=true
PARSER_SCRAPING_DELAY=2
PARSER_MAX_RETRIES=3
PARSER_TIMEOUT=30

# Logging
LOG_LEVEL=WARNING
LOG_FORMAT=json

# Sentry (optional monitoring)
SENTRY_DSN=
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1
```

### 3. Сгенерировать безопасные ключи

```bash
# Сгенерировать API ключ
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Сгенерировать пароль для БД
python3 -c "import secrets; print(secrets.token_urlsafe(24))"
```

### 4. Запустить сервисы

```bash
# Build и запуск
docker compose -f infrastructure/docker-compose.prod.yml up -d

# Проверить статус
docker compose -f infrastructure/docker-compose.prod.yml ps

# Посмотреть логи
docker compose -f infrastructure/docker-compose.prod.yml logs -f
```

### 5. Инициализировать БД (первый запуск)

```bash
# Схема применится автоматически при первом запуске PostgreSQL
# Проверьте логи
docker logs estet_postgres_prod
```

### 6. Проверить работоспособность

```bash
# Health check
curl http://localhost:8000/health

# Vision API Swagger
curl http://localhost:8000/docs

# Parser API
curl http://localhost:8001/health
```

---

## НАСТРОЙKA NGINX + SSL

### 1. Получить SSL сертификаты (Let's Encrypt)

```bash
# Установить Certbot
sudo apt install -y certbot

# Получить сертификат (требуется домен)
sudo certbot certonly --standalone -d your-domain.com -d www.your-domain.com

# Сертификаты будут в /etc/letsencrypt/live/your-domain.com/
```

### 2. Скопировать сертификаты для Docker

```bash
sudo mkdir -p /opt/estet-platform/infrastructure/nginx/ssl
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem /opt/estet-platform/infrastructure/nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem /opt/estet-platform/infrastructure/nginx/ssl/key.pem
sudo chown -R deployer:deployer /opt/estet-platform/infrastructure/nginx/ssl
```

### 3. Обновить Nginx конфиг

Отредактируйте `infrastructure/nginx/nginx.conf`, раскомментировав секцию HTTPS:

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location /api/ {
        proxy_pass http://vision_api/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 15M;
    }

    location /docs {
        proxy_pass http://vision_api/docs;
        proxy_set_header Host $host;
    }
}

# Редирект HTTP → HTTPS
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$host$request_uri;
}
```

### 4. Перезапустить Nginx

```bash
docker compose -f infrastructure/docker-compose.prod.yml restart nginx
```

### 5. Настроить автообновление SSL

```bash
# Создать скрипт обновления
sudo nano /etc/cron.d/certbot-renew

# Добавить задачу (перезапуск каждый месяц)
0 0 1 * * root certbot renew --quiet && cp /etc/letsencrypt/live/your-domain.com/*.pem /opt/estet-platform/infrastructure/nginx/ssl/ && docker restart estet_nginx
```

---

## НАСТРОЙКА CI/CD ЧЕРЕЗ GITHUB ACTIONS

### 1. Настроить Secrets в GitHub Repository

Перейдите в **Settings → Secrets and variables → Actions** и добавьте:

| Secret            | Описание                               | Пример                    |
|-------------------|----------------------------------------|---------------------------|
| `SSH_PRIVATE_KEY` | Приватный SSH ключ для доступа к серверу | `-----BEGIN OPENSSH...`   |
| `SERVER_HOST`     | IP или домен сервера                   | `192.168.1.100`           |
| `SERVER_USER`     | Пользователь для деплоя                | `deployer`                |

### 2. Создать Environment "production"

```
Settings → Environments → New environment: production
```

Добавьте переменные:
- `DEPLOY_URL`: https://your-domain.com

### 3. Автоматический деплой при push в main

Workflow `.github/workflows/deploy.yml` автоматически:
1. Запускает тесты
2. Собирает Docker образы
3. Копирует файлы на сервер через SSH
4. Перезапускает контейнеры

### 4. Ручной триггер деплоя

```bash
# Через GitHub CLI
gh workflow run deploy.yml --ref main

# Или через UI: Actions → Deploy to Production → Run workflow
```

---

## ДЕПЛОЙ БЕЗ DOCKER (РУЧНАЯ УСТАНОВКА)

### 1. Установить Python 3.11

```bash
sudo apt install -y python3.11 python3.11-venv python3.11-dev
```

### 2. Создать директорию приложения

```bash
sudo mkdir -p /opt/estet-platform
sudo chown deployer:deployer /opt/estet-platform
cd /opt/estet-platform
```

### 3. Клонировать репозиторий

```bash
git clone https://github.com/your-org/estet-platform.git .
```

### 4. Создать виртуальные окружения

```bash
# Shared package
python3.11 -m venv venv-shared
source venv-shared/bin/activate
cd packages/estet-shared
pip install -e .
cd ../..

# Vision API
python3.11 -m venv venv-vision
source venv-vision/bin/activate
cd services/vision-api
pip install -r requirements.txt
cd ../..

# Parser
python3.11 -m venv venv-parser
source venv-parser/bin/activate
cd services/parser
pip install -r requirements.txt
cd ../..
```

### 5. Настроить Environment Variables

```bash
cp .env.example .env
nano .env
# Заполнить все переменные
```

### 6. Настроить systemd сервисы

**Vision API Service:**

```bash
sudo nano /etc/systemd/system/estet-vision-api.service
```

```ini
[Unit]
Description=ESTET Vision API Service
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=deployer
Group=deployer
WorkingDirectory=/opt/estet-platform/services/vision-api
EnvironmentFile=/opt/estet-platform/.env
ExecStart=/opt/estet-platform/venv-vision/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=estet-vision-api

# Security
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

**Parser Service (cron job):**

```bash
sudo nano /etc/systemd/system/estet-parser.service
```

```ini
[Unit]
Description=ESTET Parser Service
After=network.target postgresql.service

[Service]
Type=oneshot
User=deployer
Group=deployer
WorkingDirectory=/opt/estet-platform/services/parser
EnvironmentFile=/opt/estet-platform/.env
ExecStart=/opt/estet-platform/venv-parser/bin/python scripts/run_parser.py --full
```

### 7. Запустить сервисы

```bash
# Reload systemd
sudo systemctl daemon-reload

# Включить и запустить Vision API
sudo systemctl enable estet-vision-api
sudo systemctl start estet-vision-api

# Проверить статус
sudo systemctl status estet-vision-api

# Посмотреть логи
sudo journalctl -u estet-vision-api -f
```

### 8. Настроить Cron для парсера

```bash
crontab -e

# Добавить задание (каждую субботу в 2:00)
0 2 * * 6 /opt/estet-platform/venv-parser/bin/python /opt/estet-platform/services/parser/scripts/run_parser.py --full >> /var/log/estet-parser.log 2>&1
```

Или через systemd timer:

```bash
sudo nano /etc/systemd/system/estet-parser.timer
```

```ini
[Unit]
Description=Run ESTET Parser weekly

[Timer]
OnCalendar=Sat *-*-* 02:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

```bash
sudo systemctl enable --now estet-parser.timer
systemctl list-timers | grep estet
```

### 9. Настроить Nginx как reverse proxy

```bash
sudo apt install -y nginx

sudo nano /etc/nginx/sites-available/estet-platform
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 15M;
    }

    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/estet-platform /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## МОНИТОРИНГ И ЛОГИРОВАНИЕ

### 1. Docker логи

```bash
# Все логи
docker compose -f infrastructure/docker-compose.prod.yml logs -f

# Только Vision API
docker compose -f infrastructure/docker-compose.prod.yml logs -f vision-api

# Только Parser
docker compose -f infrastructure/docker-compose.prod.yml logs -f parser
```

### 2. Настроить Sentry (опционально)

В `.env.production`:

```env
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1
```

### 3. Health Check мониторинг

```bash
# Создать скрипт проверки
nano /opt/estet-platform/scripts/health-check.sh
```

```bash
#!/bin/bash

# Health check
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)

if [ $RESPONSE -ne 200 ]; then
    echo "❌ Vision API is down! Status: $RESPONSE"
    # Перезапуск
    docker compose -f /opt/estet-platform/infrastructure/docker-compose.prod.yml restart vision-api
else
    echo "✅ Vision API is healthy"
fi
```

```bash
chmod +x /opt/estet-platform/scripts/health-check.sh
```

Добавить в cron:

```bash
*/5 * * * * /opt/estet-platform/scripts/health-check.sh >> /var/log/estet-health.log 2>&1
```

### 4. Prometheus + Grafana (опционально)

Для продвинутого мониторинга добавьте в `docker-compose.prod.yml`:

```yaml
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./infrastructure/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=your_grafana_password
    depends_on:
      - prometheus
```

---

## БЭКАПЫ И ВОССТАНОВЛЕНИЕ

### 1. Автоматические бэкапы БД

```bash
nano /opt/estet-platform/scripts/backup-db.sh
```

```bash
#!/bin/bash

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/estet-platform/backups"
mkdir -p $BACKUP_DIR

# Docker вариант
docker exec estet_postgres_prod pg_dump -U estet estet_platform > $BACKUP_DIR/db_backup_$DATE.sql

# Сжатие
gzip $BACKUP_DIR/db_backup_$DATE.sql

# Удалить старые бэкапы (> 30 дней)
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "✅ Backup created: db_backup_$DATE.sql.gz"
```

```bash
chmod +x /opt/estet-platform/scripts/backup-db.sh
```

Cron (ежедневно в 3:00):

```bash
0 3 * * * /opt/estet-platform/scripts/backup-db.sh >> /var/log/estet-backup.log 2>&1
```

### 2. Восстановление из бэкапа

```bash
# Decompress
gunzip backups/db_backup_20240101_030000.sql.gz

# Восстановить
docker exec -i estet_postgres_prod psql -U estet estet_platform < backups/db_backup_20240101_030000.sql

# Или для bare metal
psql -U estet -d estet_platform -f backups/db_backup_20240101_030000.sql
```

### 3. Бэкап изображений

```bash
tar -czf backups/images_$(date +%Y%m%d).tar.gz services/parser/data/images/
```

---

## TROUBLESHOOTING

### PostgreSQL не запускается

```bash
docker logs estet_postgres_prod

# Проверить права на volume
docker volume inspect estet-platform_postgres_data
```

### PGVector не установлен

```bash
# В контейнере PostgreSQL
docker exec -it estet_postgres_prod psql -U estet -d estet_platform -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### Vision API не отвечает

```bash
# Проверить логи
docker logs estet_vision_api_prod

# Проверить переменные окружения
docker exec estet_vision_api_prod env | grep DATABASE_URL

# Перезапустить
docker compose -f infrastructure/docker-compose.prod.yml restart vision-api
```

### Parser падает во время парсинга

```bash
# Проверить логи
docker logs estet_parser_prod

# Увеличить timeout в .env
PARSER_TIMEOUT=60

# Запустить вручную для отладки
docker exec -it estet_parser_prod python scripts/run_parser.py --product https://moscow.estetdveri.ru/product/test
```

### Nginx 502 Bad Gateway

```bash
# Проверить что Vision API запущен
docker ps | grep vision-api

# Проверить Nginx конфиг
docker exec estet_nginx nginx -t

# Перезапустить Nginx
docker compose -f infrastructure/docker-compose.prod.yml restart nginx
```

### Проблемы с SSL

```bash
# Проверить сертификат
openssl s_client -connect your-domain.com:443

# Обновить сертификат
sudo certbot renew
sudo systemctl reload nginx
```

### Очистка Docker

```bash
# Удалить неиспользуемые образы
docker image prune -a

# Удалить volumes (ОСТОРОЖНО!)
docker volume prune

# Посмотреть использование диска
docker system df
```

---

## 📝 ЧЕКЛИСТ ДЕПЛОЯ

### Подготовка
- [ ] Сервер создан и доступен
- [ ] Домен настроен на сервер
- [ ] SSL сертификат получен
- [ ] Фаервол настроен
- [ ] SSH ключи настроены

### База данных
- [ ] PostgreSQL запущен
- [ ] PGVector установлен
- [ ] Пользователь и БД созданы
- [ ] Схема применена
- [ ] Бэкапы настроены

### Приложение
- [ ] Репозиторий клонирован
- [ ] .env.production заполнен
- [ ] Docker образы собраны
- [ ] Контейнеры запущены
- [ ] Health check проходит

### Nginx
- [ ] SSL сертификаты скопированы
- [ ] Конфигурация обновлена
- [ ] HTTPS работает
- [ ] HTTP → HTTPS редирект работает

### Мониторинг
- [ ] Логи настроены
- [ ] Health check скрипт работает
- [ ] Бэкапы настроены
- [ ] Sentry подключен (опционально)

### CI/CD
- [ ] GitHub Secrets добавлены
- [ ] Workflow деплоя работает
- [ ] Ручной триггер работает

---

## 🎯 КОМАНДЫ ДЛЯ УПРАВЛЕНИЯ

### Docker Compose

```bash
# Запуск
docker compose -f infrastructure/docker-compose.prod.yml up -d

# Остановка
docker compose -f infrastructure/docker-compose.prod.yml down

# Перезапуск
docker compose -f infrastructure/docker-compose.prod.yml restart

# Логи
docker compose -f infrastructure/docker-compose.prod.yml logs -f

# Статус
docker compose -f infrastructure/docker-compose.prod.yml ps

# Обновление
docker compose -f infrastructure/docker-compose.prod.yml pull
docker compose -f infrastructure/docker-compose.prod.yml up -d --build
```

### Systemd (bare metal)

```bash
# Статус
sudo systemctl status estet-vision-api

# Перезапуск
sudo systemctl restart estet-vision-api

# Логи
sudo journalctl -u estet-vision-api -f --since "1 hour ago"
```

### Parser

```bash
# Запустить вручную
docker exec -it estet_parser_prod python scripts/run_parser.py --full

# Или bare metal
/opt/estet-platform/venv-parser/bin/python /opt/estet-platform/services/parser/scripts/run_parser.py --full
```

---

## 📞 ПОДДЕРЖКА

При возникновении проблем:

1. Проверьте логи: `docker compose logs -f`
2. Проверьте health check: `curl http://localhost:8000/health`
3. Перезапустите сервисы: `docker compose restart`
4. Проверьте FAQ выше

---

**Версия:** 1.0 | **Обновлено:** Апрель 2026

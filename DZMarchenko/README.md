# Чат-приложение (курс: современные технологии разработки ПО)

## Что сделано

- **Архитектура и ТЗ**: `docs/architecture.md`, `docs/technical_spec.md`
- **API (CRUD + JWT)**: сервисы `services/user_service` и `services/chat_service`
- **Микросервис уведомлений**: `services/notification_service` (заглушка + контракт API)
- **Контейнеризация**: `docker-compose.yml`, Dockerfile'ы сервисов
- **Тесты**: `pytest` тесты для основных эндпоинтов (JWT + CRUD)

## Быстрый старт (Docker)

1) Установите Docker Desktop.

2) В корне проекта выполните:

```bash
docker compose up --build
```

3) Сервисы:
- **user-service**: `http://localhost:8001` (OpenAPI: `/docs`)
- **chat-service**: `http://localhost:8002` (OpenAPI: `/docs`)
- **notification-service**: `http://localhost:8003` (OpenAPI: `/docs`)

## Локальный запуск (без Docker)

Требуется Python 3.11+.

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r services\user_service\requirements.txt
pip install -r services\chat_service\requirements.txt
pip install -r services\notification_service\requirements.txt
```

Запуск сервиса (пример):

```bash
uvicorn services.user_service.app.main:app --reload --port 8001
```

## Диаграмма

Диаграмма и описание компонентов см. в `docs/architecture.md`.


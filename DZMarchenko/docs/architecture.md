# Архитектура

## Выбранный подход

Выбрана **микросервисная архитектура** (минимальный набор сервисов) с взаимодействием по **REST**:

- `user-service`: регистрация, аутентификация, выпуск JWT
- `chat-service`: групповые чаты и сообщения (CRUD)
- `notification-service`: отправка уведомлений (демо/заглушка), вызывается `chat-service`

Причины выбора:
- раздельная ответственность (Users/Auth отдельно от домена чатов)
- возможность независимого масштабирования
- понятная интеграция для учебного проекта (REST, OpenAPI)

## Архитектурная диаграмма (Mermaid)

```mermaid
flowchart LR
  Client[Web/Mobile Client] -->|REST| Chat[chat-service]
  Client -->|REST| User[user-service]

  Chat -->|verify token (shared secret)| AuthLogic[JWT validation]
  Chat -->|REST| Notif[notification-service]

  User --> UserDB[(PostgreSQL user_db)]
  Chat --> ChatDB[(PostgreSQL chat_db)]
  Notif --> NotifDB[(PostgreSQL notif_db)]
```

## Компоненты

- **API**: FastAPI (OpenAPI/Swagger из коробки)
- **БД**: PostgreSQL (в Docker Compose). Для тестов — SQLite in-memory.
- **ORM**: SQLAlchemy 2.x
- **Миграции**: Alembic (подготовлены конфиги; в учебной версии можно стартовать с `create_all`)
- **Тестирование**: pytest + httpx (ASGI client)
- **Контейнеризация**: Docker + Docker Compose

## Паттерны и принципы

- **MVC (вариант для API)**: разделение на слои `routers` (контроллеры), `services` (бизнес-логика), `repositories/db` (доступ к данным), `schemas` (DTO)
- **Factory**: создание сессии БД через фабрику `get_db()` (dependency)
- **Singleton (ограниченно)**: конфигурация приложения через объект `Settings` (один источник правды)

## Взаимодействие сервисов

- `user-service` выпускает JWT (HS256).
- `chat-service` принимает JWT от клиента и валидирует его тем же секретом (shared secret через env).
- При создании сообщения `chat-service` может дернуть `notification-service` для отправки уведомления участникам чата (демо-вызов).


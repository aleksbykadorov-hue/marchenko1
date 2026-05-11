# Полная инструкция: проект DZMarchenko (чат на микросервисах)

Документ для самостоятельного изучения: что лежит в репозитории, как запустить систему и как ей пользоваться.

---

## 1. Что это за проект

Учебное **чат-приложение** в стиле микросервисов (курс «современные технологии разработки ПО»).

- Регистрация и вход пользователей, выдача **JWT**.
- **Чаты**: создание, список, участники, сообщения, удаление своего сообщения.
- **Сервис уведомлений** — упрощённая реализация: принимает события (например, при создании сообщения) и сохраняет их в БД.
- Есть **веб-страница** для ручной проверки сценария «логин → чаты → сообщения».
- **Docker Compose** поднимает три базы PostgreSQL и три сервиса разом.
- **Тесты** на `pytest` в каждом сервисе.

Теория и схемы: папка `docs/` (`architecture.md`, `technical_spec.md`).

---

## 2. Структура папок (кратко)

| Путь | Назначение |
|------|------------|
| `docs/` | Архитектура, ТЗ |
| `docker-compose.yml` | Запуск всех контейнеров |
| `services/user_service/` | Пользователи: `/auth/register`, `/auth/login`, `/me` |
| `services/chat_service/` | Чаты и сообщения + веб UI в `app/web/` |
| `services/notification_service/` | `POST /notify` — запись уведомления |
| `README.md` | Краткий быстрый старт |

В корне может быть `.venv` — локальное виртуальное окружение Python (не обязательно для Docker).

---

## 3. Требования

**Вариант A — только Docker**

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) для Windows.

**Вариант B — запуск без Docker**

- Python **3.11+**
- Установленный PostgreSQL **или** уже поднятые контейнеры только с БД (можно взять из `docker-compose` сервисы `postgres_*` отдельно).
- Утилита `uvicorn` (ставится через `pip` из `requirements.txt` сервисов).

---

## 4. Запуск через Docker (рекомендуется)

### 4.1. Команды

Откройте терминал (PowerShell) и перейдите в корень проекта:

```powershell
cd c:\Users\bykad\Desktop\Cursor\DZMarchenko
docker compose up --build
```

Первый раз образы соберутся, затем поднимутся контейнеры. Логи трёх приложений и PostgreSQL пойдут в этот же терминал.

### 4.2. Остановка

- Остановить: `Ctrl+C` в том же окне.
- Полностью убрать контейнеры (опционально): `docker compose down`  
  Тома с данными БД по умолчанию сохраняются; чтобы удалить и их: `docker compose down -v` (осторожно: потеря данных в БД).

### 4.3. Пересборка после изменений кода

```powershell
docker compose up --build
```

---

## 5. Адреса и порты после `docker compose up`

### 5.1. HTTP-сервисы (с хоста, браузер / Postman)

| Сервис | URL | Swagger UI (интерактивная документация API) |
|--------|-----|-----------------------------------------------|
| Пользователи | http://localhost:8001 | http://localhost:8001/docs |
| Чат | http://localhost:8002 | http://localhost:8002/docs |
| Уведомления | http://localhost:8003 | http://localhost:8003/docs |

Внутри Docker сеть другая: сервисы обращаются друг к другу по именам (`user-service`, `chat-service`, `notification-service`), порты внутри контейнеров — **8000**; на вашем ПК проброшены **8001–8003**, как в таблице.

### 5.2. PostgreSQL (если подключаетесь с компьютера, не из контейнера)

| База | Порт на хосте | Пользователь / пароль / БД (из compose) |
|------|----------------|-------------------------------------------|
| user_db | **5433** | `app` / `app` / `user_db` |
| chat_db | **5434** | `app` / `app` / `chat_db` |
| notif_db | **5435** | `app` / `app` / `notif_db` |

Строка подключения для SQLAlchemy/psycopg (пример для user_db):

`postgresql+psycopg://app:app@localhost:5433/user_db`

---

## 6. Веб-интерфейс чата

После запуска Compose откройте в браузере:

**http://localhost:8002/**

Страница грузится с `chat-service`. В скриптах зашиты адреса:

- пользовательский API: `http://localhost:8001`
- чат API: `http://localhost:8002`

Поэтому UI рассчитан на работу **именно с этими портами на вашей машине**.

Типовой сценарий:

1. Зарегистрироваться или войти (email + пароль).
2. Создать чат, обновить список чатов, выбрать чат.
3. Отправлять сообщения; список сообщений периодически обновляется.

Токен сохраняется в **localStorage** браузера.

---

## 7. Работа через Swagger (`/docs`)

Удобно смотреть схемы запросов и ответов и слать запросы из браузера.

### 7.1. Регистрация и токен

1. Откройте http://localhost:8001/docs .
2. `POST /auth/register` — тело: email и пароль (см. схему `RegisterIn`).
3. `POST /auth/login` — те же поля; в ответе будет `access_token`.

### 7.2. Заголовок авторизации для chat-service

Для эндпоинтов чата в Swagger нажмите **Authorize** и введите:

`Bearer <ваш_access_token>`

(слово `Bearer`, пробел, затем токен без кавычек).

Проверка профиля: `GET /me` на **user-service** с тем же заголовком `Authorization: Bearer ...`.

### 7.3. Основные операции chat-service

Все ниже — на http://localhost:8002/docs , с JWT.

| Метод | Путь | Назначение |
|-------|------|------------|
| POST | `/chats` | Создать чат (`title`) |
| GET | `/chats` | Список чатов текущего пользователя |
| POST | `/chats/{chat_id}/members` | Добавить участника (только владелец чата) |
| POST | `/chats/{chat_id}/messages` | Отправить сообщение |
| GET | `/chats/{chat_id}/messages` | Список сообщений (`limit`, `offset`) |
| DELETE | `/messages/{message_id}` | Удалить своё сообщение |

### 7.4. Уведомления

На http://localhost:8003/docs — `POST /notify` с телом по схеме сервиса. В обычном сценарии **chat-service** сам шлёт запрос на уведомление при создании сообщения (внутри Docker — на `notification-service:8000`).

---

## 8. Локальный запуск без Docker

Используйте, если хотите отлаживать код на машине без пересборки образов. Нужны три процесса + три БД (или временно SQLite по умолчанию в настройках — тогда данные не переживут перезапуск так же, как в Postgres; для учебы чаще поднимают Postgres).

### 8.1. Виртуальное окружение и зависимости

```powershell
cd c:\Users\bykad\Desktop\Cursor\DZMarchenko
python -m venv .venv
.\.venv\Scripts\activate
pip install -r services\user_service\requirements.txt
pip install -r services\chat_service\requirements.txt
pip install -r services\notification_service\requirements.txt
```

### 8.2. Переменные окружения

Сервисы читают настройки из переменных окружения (имена в стиле `DATABASE_URL`, `JWT_SECRET` и т.д. — как в `docker-compose.yml`).

Важно: **`JWT_SECRET` (и алгоритм) должны совпадать** у **user-service** и **chat-service**, иначе токен от логина не примет чат.

Для **chat-service** укажите URL уведомлений, если сервис запущен локально:

`NOTIFICATION_SERVICE_URL=http://localhost:8003`

Пример для PowerShell перед запуском user-service (если Postgres на портах из compose):

```powershell
$env:DATABASE_URL = "postgresql+psycopg://app:app@localhost:5433/user_db"
$env:JWT_SECRET = "dev-secret-change-me"
```

Аналогично для chat-service: `DATABASE_URL` на порт **5434**, плюс `JWT_SECRET` тот же, плюс `NOTIFICATION_SERVICE_URL`.

### 8.3. Запуск uvicorn (из папки каждого сервиса)

Три отдельных терминала:

```powershell
cd c:\Users\bykad\Desktop\Cursor\DZMarchenko\services\user_service
uvicorn app.main:app --reload --port 8001
```

```powershell
cd c:\Users\bykad\Desktop\Cursor\DZMarchenko\services\notification_service
uvicorn app.main:app --reload --port 8003
```

```powershell
cd c:\Users\bykad\Desktop\Cursor\DZMarchenko\services\chat_service
uvicorn app.main:app --reload --port 8002
```

Порты **8001, 8002, 8003** совпадают с тем, что ожидает веб-UI и примеры в этом документе.

> Примечание: в `README.md` указан вариант `uvicorn services.user_service.app.main:app` из корня — он работает только если корень проекта в `PYTHONPATH` и пакет `services` импортируется как модуль. Надёжнее запускать из каталога сервиса, как выше.

---

## 9. Тесты

Из каталога соответствующего сервиса (с активированным venv и установленными зависимостями):

```powershell
cd c:\Users\bykad\Desktop\Cursor\DZMarchenko\services\user_service
pytest
```

```powershell
cd c:\Users\bykad\Desktop\Cursor\DZMarchenko\services\chat_service
pytest
```

```powershell
cd c:\Users\bykad\Desktop\Cursor\DZMarchenko\services\notification_service
pytest
```

Тесты обычно используют свою конфигурацию БД (см. код тестов); для полного прогона может потребоваться соответствующее окружение.

---

## 10. Безопасность и продакшен

В `docker-compose.yml` заданы учебные пароли БД и `JWT_SECRET: dev-secret-change-me`. Для реального развёртывания их нужно заменить на секреты из переменных окружения или секрет-хранилища.

---

## 11. Куда смотреть при изучении кода

- Точки входа API: `app/main.py` в каждом сервисе.
- Модели БД: `app/models.py`.
- Схемы Pydantic: `app/schemas.py`.
- JWT и пароли: `user_service` / `chat_service` — `app/security.py`.
- Веб-клиент: `services/chat_service/app/web/` (`index.html`, `app.js`, `styles.css`).

Удачного изучения.

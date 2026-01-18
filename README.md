# Проект SPP

Веб‑приложение для загрузки, просмотра и обсуждения файлов с пользовательской и административной частью.

## Состав

- Frontend: React + Vite
- Backend: FastAPI
- БД: PostgreSQL
- Хранилище: MinIO
- Контейнеризация: Docker Compose

## Быстрый старт (Docker)

1. Скопируйте `.env.example` в `.env` и заполните значения.
2. Соберите и запустите контейнеры:

```bash
docker compose up -d --build
```

3. Проверьте доступность:
   - Frontend: http://localhost:5173
   - Backend: http://localhost:8000
   - MinIO Console: http://localhost:9001

## Переменные окружения

Минимально требуются:

- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`
- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `POSTGRES_URL`
- `MINIO_ROOT_USER`
- `MINIO_ROOT_PASSWORD`
- `MINIO_ENDPOINT`
- `MINIO_BUCKET_NAME`

## Миграции

Контейнер `alembic` выполняет миграции автоматически при старте. При необходимости:

```bash
docker compose run --rm alembic alembic -c alembic.ini upgrade head
```

## Создание суперпользователя

В проекте используется флаг `is_superuser` в таблице `users`.
Способ включения:

1. Создайте пользователя через UI.
2. В БД установите `is_superuser = true` для нужного пользователя.

Пример SQL (psql):

```sql
UPDATE users SET is_superuser = true WHERE email = 'admin@example.com';
```

## Администрирование

Админ‑страницы доступны только суперпользователям.
Проверка выполняется на backend (`/admin/me`) и в UI.

## Полезные команды

Остановка:

```bash
docker compose down
```

Логи:

```bash
docker compose logs -f backend
docker compose logs -f frontend
```

Перезапуск:

```bash
docker compose restart
```

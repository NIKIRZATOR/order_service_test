# Order Service (FastAPI)

Сервис управления заказами с JWT-auth, PostgreSQL, Redis, RabbitMQ, TaskIQ.

## Что реализовано

- Регистрация и авторизация пользователя (`/register/`, `/token/`)
- CRUD-операции с заказами по ТЗ:
  - `POST /orders/`
  - `GET /orders/{order_id}/`
  - `PATCH /orders/{order_id}/`
  - `GET /orders/user/{user_id}/`
- Кеширование заказа в Redis (TTL 5 минут)
- Публикация события `new_order` в RabbitMQ при создании заказа
- Отдельный `consumer`, который читает RabbitMQ и отправляет задачу в TaskIQ
- `worker` TaskIQ для фоновой обработки заказа
- Rate limiting (SlowAPI)
- CORS_middleware
- Alembic-миграции
- Docker Compose

## Технологии

- Python 3.12
- FastAPI
- SQLAlchemy (async) + Alembic
- PostgreSQL 16
- Redis 7
- RabbitMQ 3 (management)
- TaskIQ + taskiq-redis
- Docker / Docker Compose

## Структура проекта

```text
app/
  api/
    routes/
      auth_route.py
      orders_route.py
      default_route.py
    deps.py
  core/
    config.py
    security.py
    rate_limit.py
    redis.py
  database/
    models/
      user_model.py
      order_model.py
    session.py
    database.py
  schemas/
    auth.py
    order.py
  services/
    rabbit_publisher.py
    cache_orders.py
  consumer.py
  tasks.py
alembic/
  env.py
  versions/
docker-compose.yaml
Dockerfile
```

## Переменные окружения

Проект использует `.env` в корне.


## Запуск через Docker

1. Собрать и запустить сервисы:

```bash
docker compose up --build -d
```

2. Применить миграции:

```bash
docker compose exec api alembic upgrade head
```

3. Проверить, что сервисы запущены:

```bash
docker compose ps
```

4. Открыть Swagger UI:

- `http://127.0.0.1:8000/docs`

5. Логи:

```bash
docker compose logs -f api
docker compose logs -f consumer
docker compose logs -f worker
docker compose logs -f rabbitmq
```


## API: сценарий использования

### 1. Регистрация

`POST /register/`

Body (`application/json`):

```json
{
  "email": "123@123.com",
  "password": "123"
}
```

Ответ `201`:

```json
{
  "id": 1,
  "email": "user@example.com"
}
```

### 2. Получение JWT токена

`POST /token/`


- `username`: email
- `password`: пароль


Ответ `200`:

```json
{
  "access_token": "<JWT_TOKEN>",
  "token_type": "bearer"
}
```

### 3. Создание заказа

`POST /orders/` (требуется `Auth bearer <token>`)


```json
{
  "items": [
    {
      "name_product": "Хлеб",
      "count_product": 2,
      "price_product": 10.5
    },
    {
      "name_product": "Масло",
      "count_product": 1,
      "price_product": 5.0
    }
  ],
  "total_price": 26.0
}
```

Валидация:

- `items` не пустой
- `count_product > 0`
- `price_product > 0`
- `total_price > 0`
- `total_price` должен совпадать с суммой по товарам

Ответ `201`:

```json
{
  "id": "d04ba9a6-a9b0-4696-b3c6-f077f58f7f7c",
  "user_id": 1,
  "items": [
    {"name_product": "Хлеб", "count_product": 2, "price_product": 10.5},
    {"name_product": "Масло", "count_product": 1, "price_product": 5.0}
  ],
  "total_price": 26.0,
  "status": "PENDING",
  "created_at": "2026-02-10T18:00:00.000000+00:00"
}
```

### 4. Получить заказ по ID

`GET /orders/{order_id}/`

Сервис сначала читает из Redis, при промахе идет в PostgreSQL и кладет результат в кеш.

### 5. Обновить статус заказа

`PATCH /orders/{order_id}/`

Допустимые статусы: `PENDING`, `PAID`, `SHIPPED`, `CANCELED`.

### 6. Получить заказы пользователя

`GET /orders/user/{user_id}/` ( `user_id` должен совпадать с id пользователя в токене, можно узнать через GET /fetch_me/)

### 7. Вспомогательные эндпоинты

- `GET /fetch_me/` - вернуть текущего пользователя
- `GET /home/database/` - проверка подключения к БД (диагностический endpoint)


## Rate limits (текущее поведение)

- Общий лимит: `100/minute`
- `POST /register/`: `5/minute`
- `POST /token/`: `5/minute`
- `POST /orders/`: `10/minute`
- `GET /orders/{order_id}/`: `10/minute`
- `PATCH /orders/{order_id}/`: `20/minute`
- `GET /orders/user/{user_id}/`: `20/minute`
- `GET /home/database/`: `1/minute`
- `GET /fetch_me/`: `10/minute`

## event-bus и фоновые задачи 

1. Создать заказ через API.
2. Проверить логи `api`: должна быть публикация в RabbitMQ.
3. Проверить логи `consumer`: получение `new_order` и отправка задачи в TaskIQ.
4. Проверить логи `worker`: сообщения `Processing order ...` и `Order ... processed`.

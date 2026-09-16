# Transport Company Automation

Серверное приложение для автоматизации транспортной компании, специализирующейся на дальнобойных грузоперевозках.

## Стек

- FastAPI
- SQLAlchemy ORM 2.x
- SQLite по умолчанию
- PostgreSQL через замену `DATABASE_URL`
- Jinja2 для простого серверного веб-интерфейса

## Запуск

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Откройте:

- Клиентское окно: http://127.0.0.1:8000
- Настройки / вход администратора: http://127.0.0.1:8000/settings
- Админ-панель: http://127.0.0.1:8000/admin
- Конструктор клиентского окна: http://127.0.0.1:8000/admin/client-window
- Swagger/OpenAPI: http://127.0.0.1:8000/docs

При первом запуске SQLite-база `transport.db` создаётся автоматически вместе с демо-данными.

Пароль администратора по умолчанию: `admin123`.

Для смены пароля задайте переменную окружения:

```bash
set ADMIN_PASSWORD=your_password
```

Без входа администратора пользователь видит только простое клиентское окно для подачи заявки.

`/docs` - это техническая страница FastAPI для проверки REST API разработчиком. В пользовательском меню она не показывается.

## 3D-модель машины

В карточках машин есть 3D-просмотр. По умолчанию используется встроенная простая модель.

Чтобы поставить свою бесплатную модель, положите DAE-файл сюда:

```text
app/static/models/model.dae
```

или GLB-файл сюда:

```text
app/static/models/truck.glb
```

Ссылки на бесплатные варианты: [docs/3d-models.md](docs/3d-models.md).

## PostgreSQL

Код использует SQLAlchemy без SQLite-специфичной бизнес-логики. Для PostgreSQL задайте:

```bash
set DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/transport
```

и установите драйвер:

```bash
pip install "psycopg[binary]"
```

## Основные REST-эндпоинты

- `GET/POST /api/vehicles`
- `GET/PUT/DELETE /api/vehicles/{vehicle_id}`
- `GET/POST /api/drivers`
- `GET/PUT/DELETE /api/drivers/{driver_id}`
- `GET/POST /api/clients`
- `GET/PUT/DELETE /api/clients/{client_id}`
- `GET/POST /api/cargo-requests`
- `GET/PUT/DELETE /api/cargo-requests/{request_id}`
- `POST /api/matching/vehicles`
- `GET /api/cargo-requests/{request_id}/matching`
- `GET/POST /api/orders`
- `POST /api/orders/{order_id}/start`
- `POST /api/orders/{order_id}/complete`
- `GET /api/reports/trips`
- `GET /api/reports/vehicle-utilization`
- `GET /api/reports/income-by-clients`
- `GET /api/reports/income-by-vehicles`
- `GET /api/reports/top-vehicles`

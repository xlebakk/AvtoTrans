# Transport Company Automation

Веб-приложение для автоматизации работы транспортной компании, которая занимается дальними грузоперевозками.

## Возможности

- клиентское окно для подачи заявок на перевозку;
- административная панель для управления заказами, рейсами, автопарком, водителями и клиентами;
- подбор подходящих автомобилей для заявки;
- контроль статусов рейсов и обновление местоположения водителей;
- отчёты по рейсам, загрузке автопарка и доходам;
- интерактивная карта маршрутов с расчётом расстояния;
- конструктор клиентского окна;
- REST API и интерактивная документация OpenAPI.

## Технологии

- Python 3.11+
- FastAPI
- SQLAlchemy 2.x
- Jinja2
- SQLite по умолчанию
- PostgreSQL через переменную `DATABASE_URL`
- Leaflet и Three.js для карты и 3D-просмотра

## Быстрый старт

Создайте виртуальное окружение и установите зависимости:

```bash
python -m venv .venv
```

Windows:

```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Linux и macOS:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

Запустите приложение:

```bash
uvicorn app.main:app --reload
```

После запуска доступны следующие страницы:

| Раздел | Адрес |
| --- | --- |
| Клиентское окно | `http://127.0.0.1:8000/` |
| Настройки и вход администратора | `http://127.0.0.1:8000/settings` |
| Административная панель | `http://127.0.0.1:8000/admin` |
| Конструктор клиентского окна | `http://127.0.0.1:8000/admin/client-window` |
| Swagger / OpenAPI | `http://127.0.0.1:8000/docs` |

Локальная база данных `transport.db` создаётся автоматически при первом запуске. Файл базы данных не входит в репозиторий.

## Конфигурация

Пароль администратора задаётся переменной окружения `ADMIN_PASSWORD`. Если переменная не указана, приложение использует значение по умолчанию только для локальной разработки.

Windows PowerShell:

```powershell
$env:ADMIN_PASSWORD = "your_password"
```

Linux и macOS:

```bash
export ADMIN_PASSWORD=your_password
```

Для подключения PostgreSQL задайте `DATABASE_URL` и установите драйвер:

```bash
pip install "psycopg[binary]"
```

```text
postgresql+psycopg://user:password@localhost:5432/transport
```

## 3D-модель

В карточках автомобилей предусмотрен 3D-просмотр. По умолчанию используется встроенная простая модель.

Дополнительные варианты подключения моделей описаны в [docs/3d-models.md](docs/3d-models.md). Файлы моделей не включаются в репозиторий из-за большого размера.

## Структура проекта

```text
app/
├── routers/       Маршруты веб-интерфейса и REST API
├── services/      Прикладная логика
├── static/        JavaScript, CSS, карта и 3D-компоненты
├── templates/     Jinja2-шаблоны
├── database.py    Подключение к базе данных
├── models.py      Модели SQLAlchemy
└── schemas.py     Схемы валидации API
docs/              Дополнительная документация
requirements.txt   Зависимости Python
```

## Основные API-маршруты

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

## Лицензия

Лицензия проекта пока не определена.

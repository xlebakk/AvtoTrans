from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, text

from app.database import Base, DATABASE_URL, SessionLocal, engine
from app.routers import cargo_requests, clients, drivers, matching, orders, reports, vehicles, web
from app.routers import driver as driver_router
from app.seed import seed_demo_data


def apply_dev_migrations() -> None:
    if not DATABASE_URL.startswith("sqlite"):
        return

    inspector = inspect(engine)

    if "cargo_requests" in inspector.get_table_names():
        existing = {c["name"] for c in inspector.get_columns("cargo_requests")}
        cargo_cols = {
            "cargo_name": "VARCHAR(160)",
            "cargo_features": "TEXT",
            "origin_lat": "FLOAT",
            "origin_lng": "FLOAT",
            "destination_lat": "FLOAT",
            "destination_lng": "FLOAT",
        }
        with engine.begin() as conn:
            for name, ctype in cargo_cols.items():
                if name not in existing:
                    conn.execute(text(f"ALTER TABLE cargo_requests ADD COLUMN {name} {ctype}"))

    if "vehicles" in inspector.get_table_names():
        existing = {c["name"] for c in inspector.get_columns("vehicles")}
        vehicle_cols = {
            "fuel_consumption_per_100km": "FLOAT DEFAULT 25.0",
            "fuel_price_per_liter": "FLOAT DEFAULT 55.0",
        }
        with engine.begin() as conn:
            for name, ctype in vehicle_cols.items():
                if name not in existing:
                    conn.execute(text(f"ALTER TABLE vehicles ADD COLUMN {name} {ctype}"))

    if "orders" in inspector.get_table_names():
        existing = {c["name"] for c in inspector.get_columns("orders")}
        order_cols = {
            "fuel_cost": "FLOAT DEFAULT 0.0",
            "other_costs": "FLOAT DEFAULT 0.0",
            "profit": "FLOAT DEFAULT 0.0",
            "departure_time": "VARCHAR(5)",
        }
        with engine.begin() as conn:
            for name, ctype in order_cols.items():
                if name not in existing:
                    conn.execute(text(f"ALTER TABLE orders ADD COLUMN {name} {ctype}"))

    if "drivers" in inspector.get_table_names():
        existing = {c["name"] for c in inspector.get_columns("drivers")}
        driver_cols = {
            "password": "VARCHAR(128)",
            "last_lat": "FLOAT",
            "last_lon": "FLOAT",
            "last_seen": "DATETIME",
        }
        with engine.begin() as conn:
            for name, ctype in driver_cols.items():
                if name not in existing:
                    conn.execute(text(f"ALTER TABLE drivers ADD COLUMN {name} {ctype}"))

    if "chat_messages" in inspector.get_table_names():
        cols = {c["name"]: c for c in inspector.get_columns("chat_messages")}
        order_col = cols.get("order_id")
        if order_col and not order_col.get("nullable", True):
            with engine.begin() as conn:
                conn.execute(text(
                    "CREATE TABLE IF NOT EXISTS chat_messages_new ("
                    "  id INTEGER PRIMARY KEY, "
                    "  order_id INTEGER REFERENCES orders(id), "
                    "  driver_id INTEGER NOT NULL REFERENCES drivers(id), "
                    "  sender VARCHAR(10) NOT NULL, "
                    "  text TEXT NOT NULL, "
                    "  is_read BOOLEAN DEFAULT 0 NOT NULL, "
                    "  created_at DATETIME"
                    ")"
                ))
                conn.execute(text(
                    "INSERT INTO chat_messages_new SELECT id, order_id, driver_id, sender, text, is_read, created_at FROM chat_messages"
                ))
                conn.execute(text("DROP TABLE chat_messages"))
                conn.execute(text("ALTER TABLE chat_messages_new RENAME TO chat_messages"))


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    apply_dev_migrations()
    with SessionLocal() as db:
        seed_demo_data(db)
    yield


app = FastAPI(
    title="Автоматизация транспортной компании",
    description="Внутренняя система управления грузоперевозками: водители, грузовики, рейсы, расходы, прибыль.",
    version="1.0.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(web.router)
app.include_router(driver_router.router)
app.include_router(vehicles.router)
app.include_router(drivers.router)
app.include_router(clients.router)
app.include_router(cargo_requests.router)
app.include_router(matching.router)
app.include_router(orders.router)
app.include_router(reports.router)

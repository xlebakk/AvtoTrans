from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum

from sqlalchemy import Boolean, Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class VehicleStatus(StrEnum):
    available = "свободна"
    in_trip = "в рейсе"
    maintenance = "на ТО"


class DriverStatus(StrEnum):
    available = "свободен"
    in_trip = "в рейсе"
    rest = "отдых"


class OrderStatus(StrEnum):
    new = "новый"
    assigned = "назначен"
    arrived = "подъехал"       # Водитель прибыл к точке загрузки
    in_transit = "в пути"      # Водитель выехал с грузом
    delivered = "доставлен"


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    plate_number: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    brand: Mapped[str] = mapped_column(String(120), nullable=False)
    length_m: Mapped[float] = mapped_column(Float, nullable=False)
    width_m: Mapped[float] = mapped_column(Float, nullable=False)
    height_m: Mapped[float] = mapped_column(Float, nullable=False)
    volume_cubic_m: Mapped[float] = mapped_column(Float, nullable=False)
    capacity_kg: Mapped[float] = mapped_column(Float, nullable=False)
    base_rate_per_km: Mapped[float] = mapped_column(Float, nullable=False)
    fuel_consumption_per_100km: Mapped[float] = mapped_column(Float, nullable=False, default=25.0)
    fuel_price_per_liter: Mapped[float] = mapped_column(Float, nullable=False, default=55.0)
    status: Mapped[VehicleStatus] = mapped_column(
        Enum(VehicleStatus, native_enum=False), default=VehicleStatus.available, nullable=False
    )

    drivers: Mapped[list[Driver]] = relationship(back_populates="assigned_vehicle")
    orders: Mapped[list[Order]] = relationship(back_populates="vehicle")


class Driver(Base):
    __tablename__ = "drivers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(160), nullable=False)
    license_category: Mapped[str] = mapped_column(String(20), nullable=False)
    experience_years: Mapped[int] = mapped_column(Integer, nullable=False)
    assigned_vehicle_id: Mapped[int | None] = mapped_column(ForeignKey("vehicles.id"), nullable=True)
    status: Mapped[DriverStatus] = mapped_column(
        Enum(DriverStatus, native_enum=False), default=DriverStatus.available, nullable=False
    )
    password: Mapped[str | None] = mapped_column(String(128), nullable=True)  # plain-text для MVP
    last_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_seen: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    assigned_vehicle: Mapped[Vehicle | None] = relationship(back_populates="drivers")
    orders: Mapped[list[Order]] = relationship(back_populates="driver")
    chat_messages: Mapped[list[ChatMessage]] = relationship(back_populates="driver")


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    contacts: Mapped[str] = mapped_column(Text, nullable=False)

    cargo_requests: Mapped[list[CargoRequest]] = relationship(back_populates="client")


class CargoRequest(Base):
    __tablename__ = "cargo_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False)
    cargo_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    cargo_features: Mapped[str | None] = mapped_column(Text, nullable=True)
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False)
    length_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    width_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    height_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    volume_cubic_m: Mapped[float] = mapped_column(Float, nullable=False)
    origin: Mapped[str] = mapped_column(String(160), nullable=False)
    origin_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    origin_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    destination: Mapped[str | None] = mapped_column(String(160), nullable=True)
    destination_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    destination_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    client: Mapped[Client] = relationship(back_populates="cargo_requests")
    order: Mapped[Order | None] = relationship(back_populates="cargo_request")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    cargo_request_id: Mapped[int] = mapped_column(ForeignKey("cargo_requests.id"), unique=True, nullable=False)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"), nullable=False)
    driver_id: Mapped[int] = mapped_column(ForeignKey("drivers.id"), nullable=False)
    distance_km: Mapped[float] = mapped_column(Float, nullable=False)
    final_price: Mapped[float] = mapped_column(Float, nullable=False)
    fuel_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    other_costs: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    profit: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, native_enum=False), default=OrderStatus.assigned, nullable=False
    )
    departure_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    departure_time: Mapped[str | None] = mapped_column(String(5), nullable=True)  # "HH:MM"
    delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    cargo_request: Mapped[CargoRequest] = relationship(back_populates="order")
    vehicle: Mapped[Vehicle] = relationship(back_populates="orders")
    driver: Mapped[Driver] = relationship(back_populates="orders")
    chat_messages: Mapped[list[ChatMessage]] = relationship(back_populates="order")


class ChatMessage(Base):
    """Сообщения чата между водителем и поддержкой (admin)."""
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id: Mapped[int | None] = mapped_column(ForeignKey("orders.id"), nullable=True, index=True)  # None = общий чат
    driver_id: Mapped[int] = mapped_column(ForeignKey("drivers.id"), nullable=False)
    sender: Mapped[str] = mapped_column(String(10), nullable=False)  # "driver" | "admin"
    text: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    order: Mapped[Order | None] = relationship(back_populates="chat_messages")
    driver: Mapped[Driver] = relationship(back_populates="chat_messages")

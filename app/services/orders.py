from datetime import date

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CargoRequest, Driver, DriverStatus, Order, OrderStatus, Vehicle, VehicleStatus
from app.schemas import OrderCreate
from app.services.common import get_or_404
from app.services.routes import require_distance


BUSY_ORDER_STATUSES = (OrderStatus.assigned, OrderStatus.arrived, OrderStatus.in_transit)


def ensure_not_busy(db: Session, vehicle_id: int, driver_id: int) -> None:
    vehicle_busy_order = db.scalar(
        select(Order).where(Order.vehicle_id == vehicle_id, Order.status.in_(BUSY_ORDER_STATUSES)).limit(1)
    )
    if vehicle_busy_order is not None:
        raise HTTPException(status_code=409, detail="Машина уже занята в другом рейсе")

    driver_busy_order = db.scalar(
        select(Order).where(Order.driver_id == driver_id, Order.status.in_(BUSY_ORDER_STATUSES)).limit(1)
    )
    if driver_busy_order is not None:
        raise HTTPException(status_code=409, detail="Водитель уже занят в другом рейсе")


def create_order(db: Session, payload: OrderCreate) -> Order:
    cargo_request = get_or_404(db, CargoRequest, payload.cargo_request_id, "Заявка")
    vehicle = get_or_404(db, Vehicle, payload.vehicle_id, "Машина")
    driver = get_or_404(db, Driver, payload.driver_id, "Водитель")

    if cargo_request.order is not None:
        raise HTTPException(status_code=409, detail="Для этой заявки уже создан заказ")
    if vehicle.status != VehicleStatus.available:
        raise HTTPException(status_code=409, detail="Машина недоступна")
    if driver.status != DriverStatus.available:
        raise HTTPException(status_code=409, detail="Водитель недоступен")
    if cargo_request.volume_cubic_m > vehicle.volume_cubic_m or cargo_request.weight_kg > vehicle.capacity_kg:
        raise HTTPException(status_code=409, detail="Машина не подходит по объёму или грузоподъёмности")

    ensure_not_busy(db, vehicle.id, driver.id)
    distance_km = require_distance(cargo_request.origin, cargo_request.destination, payload.distance_km)
    final_price = round(distance_km * vehicle.base_rate_per_km, 2)
    fuel_cost = round(distance_km * vehicle.fuel_consumption_per_100km / 100 * vehicle.fuel_price_per_liter, 2)
    other_costs = round(payload.other_costs, 2)
    profit = round(final_price - fuel_cost - other_costs, 2)

    order = Order(
        cargo_request_id=cargo_request.id,
        vehicle_id=vehicle.id,
        driver_id=driver.id,
        distance_km=distance_km,
        final_price=final_price,
        fuel_cost=fuel_cost,
        other_costs=other_costs,
        profit=profit,
        status=OrderStatus.assigned,
        departure_date=payload.departure_date,
        departure_time=payload.departure_time,
    )
    vehicle.status = VehicleStatus.in_trip
    driver.status = DriverStatus.in_trip
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def start_order(db: Session, order_id: int) -> Order:
    order = get_or_404(db, Order, order_id, "Заказ")
    if order.status not in (OrderStatus.new, OrderStatus.assigned, OrderStatus.arrived):
        raise HTTPException(status_code=409, detail="В путь можно отправить только новый, назначенный или подъехавший заказ")
    order.status = OrderStatus.in_transit
    if order.departure_date is None:
        order.departure_date = date.today()
    order.vehicle.status = VehicleStatus.in_trip
    order.driver.status = DriverStatus.in_trip
    db.commit()
    db.refresh(order)
    return order


def complete_order(db: Session, order_id: int) -> Order:
    order = get_or_404(db, Order, order_id, "Заказ")
    if order.status == OrderStatus.delivered:
        return order
    if order.status not in (OrderStatus.assigned, OrderStatus.arrived, OrderStatus.in_transit):
        raise HTTPException(status_code=409, detail="Завершить можно только назначенный заказ или заказ в пути")

    order.status = OrderStatus.delivered
    order.delivery_date = date.today()
    order.vehicle.status = VehicleStatus.available
    order.driver.status = DriverStatus.available
    db.commit()
    db.refresh(order)
    return order


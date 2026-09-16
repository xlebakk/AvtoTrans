from datetime import date

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models import CargoRequest, Client, Order, Vehicle
from app.schemas import IncomeByClientRow, TripReportRow, VehicleUtilizationRow

MONTHS_RU = {
    1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
    5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
    9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь",
}


def _period_filter(statement: Select, date_from: date | None, date_to: date | None) -> Select:
    if date_from is not None:
        statement = statement.where(Order.departure_date >= date_from)
    if date_to is not None:
        statement = statement.where(Order.departure_date <= date_to)
    return statement


def trips_for_period(db: Session, date_from: date | None, date_to: date | None) -> list[TripReportRow]:
    statement = (
        select(Order)
        .join(Order.cargo_request)
        .join(CargoRequest.client)
        .join(Order.vehicle)
        .join(Order.driver)
        .order_by(Order.departure_date.desc().nullslast(), Order.created_at.desc())
    )
    statement = _period_filter(statement, date_from, date_to)
    orders = db.scalars(statement).all()

    return [
        TripReportRow(
            order_id=order.id,
            client_name=order.cargo_request.client.name,
            vehicle_plate=order.vehicle.plate_number,
            driver_name=order.driver.full_name,
            origin=order.cargo_request.origin,
            destination=order.cargo_request.destination or "не указана",
            distance_km=order.distance_km,
            final_price=order.final_price,
            fuel_cost=order.fuel_cost,
            other_costs=order.other_costs,
            profit=order.profit,
            status=order.status,
            departure_date=order.departure_date,
            delivery_date=order.delivery_date,
        )
        for order in orders
    ]


def monthly_stats(db: Session) -> list[dict]:
    """Агрегированная статистика по месяцам для графиков."""
    statement = (
        select(
            func.strftime("%Y-%m", Order.departure_date).label("month_key"),
            func.coalesce(func.sum(Order.final_price), 0).label("income"),
            func.coalesce(func.sum(Order.fuel_cost), 0).label("fuel"),
            func.coalesce(func.sum(Order.other_costs), 0).label("other"),
            func.coalesce(func.sum(Order.profit), 0).label("profit"),
            func.count(Order.id).label("trips"),
        )
        .where(Order.departure_date.isnot(None))
        .group_by(func.strftime("%Y-%m", Order.departure_date))
        .order_by(func.strftime("%Y-%m", Order.departure_date).asc())
    )
    rows = db.execute(statement).all()
    result = []
    for row in rows:
        if not row.month_key:
            continue
        year, month = map(int, row.month_key.split("-"))
        result.append({
            "month_key": row.month_key,
            "month_label": f"{MONTHS_RU.get(month, month)} {year}",
            "income": round(float(row.income), 0),
            "fuel": round(float(row.fuel), 0),
            "other": round(float(row.other), 0),
            "profit": round(float(row.profit), 0),
            "trips": row.trips,
        })
    return result


def vehicle_utilization(db: Session, limit: int | None = None) -> list[VehicleUtilizationRow]:
    statement = (
        select(
            Vehicle.id,
            Vehicle.plate_number,
            Vehicle.brand,
            func.count(Order.id).label("trips_count"),
            func.coalesce(func.sum(Order.distance_km), 0).label("total_distance_km"),
            func.coalesce(func.sum(Order.final_price), 0).label("total_income"),
            func.coalesce(func.sum(Order.fuel_cost), 0).label("total_fuel_cost"),
            func.coalesce(func.sum(Order.other_costs), 0).label("total_other_costs"),
            func.coalesce(func.sum(Order.profit), 0).label("total_profit"),
        )
        .outerjoin(Order, Order.vehicle_id == Vehicle.id)
        .group_by(Vehicle.id, Vehicle.plate_number, Vehicle.brand)
        .order_by(func.count(Order.id).desc(), func.coalesce(func.sum(Order.distance_km), 0).desc())
    )
    if limit is not None:
        statement = statement.limit(limit)

    rows = db.execute(statement).all()
    return [
        VehicleUtilizationRow(
            vehicle_id=row.id,
            plate_number=row.plate_number,
            brand=row.brand,
            trips_count=row.trips_count,
            total_distance_km=float(row.total_distance_km or 0),
            total_income=float(row.total_income or 0),
            total_fuel_cost=float(row.total_fuel_cost or 0),
            total_other_costs=float(row.total_other_costs or 0),
            total_profit=float(row.total_profit or 0),
        )
        for row in rows
    ]


def income_by_clients(db: Session) -> list[IncomeByClientRow]:
    statement = (
        select(
            Client.id,
            Client.name,
            func.count(Order.id).label("orders_count"),
            func.coalesce(func.sum(Order.final_price), 0).label("total_income"),
        )
        .join(CargoRequest, CargoRequest.client_id == Client.id)
        .join(Order, Order.cargo_request_id == CargoRequest.id)
        .group_by(Client.id, Client.name)
        .order_by(func.coalesce(func.sum(Order.final_price), 0).desc())
    )
    rows = db.execute(statement).all()
    return [
        IncomeByClientRow(
            client_id=row.id,
            client_name=row.name,
            orders_count=row.orders_count,
            total_income=float(row.total_income or 0),
        )
        for row in rows
    ]

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Client, Driver, Vehicle


def get_or_404(db: Session, model: type, object_id: int, name: str):
    entity = db.get(model, object_id)
    if entity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{name} не найден")
    return entity


def ensure_vehicle_exists(db: Session, vehicle_id: int | None) -> None:
    if vehicle_id is not None and db.get(Vehicle, vehicle_id) is None:
        raise HTTPException(status_code=404, detail="Закреплённая машина не найдена")


def ensure_client_exists(db: Session, client_id: int) -> None:
    if db.get(Client, client_id) is None:
        raise HTTPException(status_code=404, detail="Клиент не найден")


def ensure_driver_exists(db: Session, driver_id: int) -> None:
    if db.get(Driver, driver_id) is None:
        raise HTTPException(status_code=404, detail="Водитель не найден")


def calculate_volume(
    length_m: float | None,
    width_m: float | None,
    height_m: float | None,
    volume: float | None,
    allow_unknown: bool = False,
) -> float:
    if volume is not None:
        return round(volume, 3)
    if length_m is None or width_m is None or height_m is None:
        if allow_unknown:
            return 0
        raise HTTPException(status_code=422, detail="Для расчёта объёма нужны длина, ширина и высота")
    return round(length_m * width_m * height_m, 3)

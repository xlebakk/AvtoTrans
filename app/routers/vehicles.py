from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Vehicle
from app.schemas import VehicleCreate, VehicleRead, VehicleUpdate
from app.services.common import calculate_volume, get_or_404

router = APIRouter(prefix="/api/vehicles", tags=["vehicles"])


@router.get("", response_model=list[VehicleRead])
def list_vehicles(db: Session = Depends(get_db)) -> list[Vehicle]:
    return list(db.scalars(select(Vehicle).order_by(Vehicle.id)))


@router.post("", response_model=VehicleRead, status_code=201)
def create_vehicle(payload: VehicleCreate, db: Session = Depends(get_db)) -> Vehicle:
    data = payload.model_dump()
    data["volume_cubic_m"] = calculate_volume(
        payload.length_m, payload.width_m, payload.height_m, payload.volume_cubic_m
    )
    vehicle = Vehicle(**data)
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return vehicle


@router.get("/{vehicle_id}", response_model=VehicleRead)
def get_vehicle(vehicle_id: int, db: Session = Depends(get_db)) -> Vehicle:
    return get_or_404(db, Vehicle, vehicle_id, "Машина")


@router.put("/{vehicle_id}", response_model=VehicleRead)
def update_vehicle(vehicle_id: int, payload: VehicleUpdate, db: Session = Depends(get_db)) -> Vehicle:
    vehicle = get_or_404(db, Vehicle, vehicle_id, "Машина")
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(vehicle, field, value)
    if "volume_cubic_m" not in data and {"length_m", "width_m", "height_m"} & data.keys():
        vehicle.volume_cubic_m = calculate_volume(vehicle.length_m, vehicle.width_m, vehicle.height_m, None)
    db.commit()
    db.refresh(vehicle)
    return vehicle


@router.delete("/{vehicle_id}", status_code=204)
def delete_vehicle(vehicle_id: int, db: Session = Depends(get_db)) -> None:
    vehicle = get_or_404(db, Vehicle, vehicle_id, "Машина")
    db.delete(vehicle)
    db.commit()


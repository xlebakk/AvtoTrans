from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Driver
from app.schemas import DriverCreate, DriverRead, DriverUpdate
from app.services.common import ensure_vehicle_exists, get_or_404

router = APIRouter(prefix="/api/drivers", tags=["drivers"])


@router.get("", response_model=list[DriverRead])
def list_drivers(db: Session = Depends(get_db)) -> list[Driver]:
    return list(db.scalars(select(Driver).order_by(Driver.id)))


@router.post("", response_model=DriverRead, status_code=201)
def create_driver(payload: DriverCreate, db: Session = Depends(get_db)) -> Driver:
    ensure_vehicle_exists(db, payload.assigned_vehicle_id)
    driver = Driver(**payload.model_dump())
    db.add(driver)
    db.commit()
    db.refresh(driver)
    return driver


@router.get("/{driver_id}", response_model=DriverRead)
def get_driver(driver_id: int, db: Session = Depends(get_db)) -> Driver:
    return get_or_404(db, Driver, driver_id, "Водитель")


@router.put("/{driver_id}", response_model=DriverRead)
def update_driver(driver_id: int, payload: DriverUpdate, db: Session = Depends(get_db)) -> Driver:
    driver = get_or_404(db, Driver, driver_id, "Водитель")
    data = payload.model_dump(exclude_unset=True)
    ensure_vehicle_exists(db, data.get("assigned_vehicle_id"))
    for field, value in data.items():
        setattr(driver, field, value)
    db.commit()
    db.refresh(driver)
    return driver


@router.delete("/{driver_id}", status_code=204)
def delete_driver(driver_id: int, db: Session = Depends(get_db)) -> None:
    driver = get_or_404(db, Driver, driver_id, "Водитель")
    db.delete(driver)
    db.commit()


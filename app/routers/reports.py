from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import IncomeByClientRow, TripReportRow, VehicleUtilizationRow
from app.services.reports import income_by_clients, trips_for_period, vehicle_utilization

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/trips", response_model=list[TripReportRow])
def trips_report(
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[TripReportRow]:
    return trips_for_period(db, date_from, date_to)


@router.get("/vehicle-utilization", response_model=list[VehicleUtilizationRow])
def vehicle_utilization_report(db: Session = Depends(get_db)) -> list[VehicleUtilizationRow]:
    return vehicle_utilization(db)


@router.get("/income-by-clients", response_model=list[IncomeByClientRow])
def income_by_clients_report(db: Session = Depends(get_db)) -> list[IncomeByClientRow]:
    return income_by_clients(db)


@router.get("/income-by-vehicles", response_model=list[VehicleUtilizationRow])
def income_by_vehicles_report(db: Session = Depends(get_db)) -> list[VehicleUtilizationRow]:
    return vehicle_utilization(db)


@router.get("/top-vehicles", response_model=list[VehicleUtilizationRow])
def top_vehicles_report(limit: int = Query(default=5, ge=1, le=50), db: Session = Depends(get_db)) -> list[VehicleUtilizationRow]:
    return vehicle_utilization(db, limit=limit)


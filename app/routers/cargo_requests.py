from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import CargoRequest
from app.schemas import CargoRequestCreate, CargoRequestRead, CargoRequestUpdate, VehicleMatchRead, VehicleMatchRequest
from app.services.common import calculate_volume, ensure_client_exists, get_or_404
from app.services.matching import find_matching_vehicles

router = APIRouter(prefix="/api/cargo-requests", tags=["cargo requests"])


@router.get("", response_model=list[CargoRequestRead])
def list_cargo_requests(db: Session = Depends(get_db)) -> list[CargoRequest]:
    return list(db.scalars(select(CargoRequest).order_by(CargoRequest.created_at.desc())))


@router.post("", response_model=CargoRequestRead, status_code=201)
def create_cargo_request(payload: CargoRequestCreate, db: Session = Depends(get_db)) -> CargoRequest:
    ensure_client_exists(db, payload.client_id)
    data = payload.model_dump()
    data["destination"] = payload.destination or ""
    data["volume_cubic_m"] = calculate_volume(
        payload.length_m, payload.width_m, payload.height_m, payload.volume_cubic_m, allow_unknown=True
    )
    request = CargoRequest(**data)
    db.add(request)
    db.commit()
    db.refresh(request)
    return request


@router.get("/{request_id}", response_model=CargoRequestRead)
def get_cargo_request(request_id: int, db: Session = Depends(get_db)) -> CargoRequest:
    return get_or_404(db, CargoRequest, request_id, "Заявка")


@router.put("/{request_id}", response_model=CargoRequestRead)
def update_cargo_request(
    request_id: int, payload: CargoRequestUpdate, db: Session = Depends(get_db)
) -> CargoRequest:
    request = get_or_404(db, CargoRequest, request_id, "Заявка")
    data = payload.model_dump(exclude_unset=True)
    if data.get("destination") is None:
        data["destination"] = ""
    if "client_id" in data:
        ensure_client_exists(db, data["client_id"])
    for field, value in data.items():
        setattr(request, field, value)
    if "volume_cubic_m" not in data and {"length_m", "width_m", "height_m"} & data.keys():
        request.volume_cubic_m = calculate_volume(
            request.length_m, request.width_m, request.height_m, None, allow_unknown=True
        )
    db.commit()
    db.refresh(request)
    return request


@router.delete("/{request_id}", status_code=204)
def delete_cargo_request(request_id: int, db: Session = Depends(get_db)) -> None:
    request = get_or_404(db, CargoRequest, request_id, "Заявка")
    db.delete(request)
    db.commit()


@router.get("/{request_id}/matching", response_model=list[VehicleMatchRead])
def match_for_cargo_request(request_id: int, db: Session = Depends(get_db)) -> list[VehicleMatchRead]:
    request = get_or_404(db, CargoRequest, request_id, "Заявка")
    payload = VehicleMatchRequest(
        weight_kg=request.weight_kg,
        volume_cubic_m=request.volume_cubic_m or None,
        origin=request.origin,
        destination=request.destination or None,
    )
    return find_matching_vehicles(db, payload)

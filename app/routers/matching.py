from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import VehicleMatchRead, VehicleMatchRequest
from app.services.matching import find_matching_vehicles

router = APIRouter(prefix="/api/matching", tags=["matching"])


@router.post("/vehicles", response_model=list[VehicleMatchRead])
def match_vehicles(payload: VehicleMatchRequest, db: Session = Depends(get_db)) -> list[VehicleMatchRead]:
    return find_matching_vehicles(db, payload)


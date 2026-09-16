from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Vehicle, VehicleStatus
from app.schemas import VehicleMatchRead, VehicleMatchRequest, VehicleRead
from app.services.common import calculate_volume
from app.services.routes import get_known_distance


def find_matching_vehicles(db: Session, payload: VehicleMatchRequest) -> list[VehicleMatchRead]:
    required_volume = calculate_volume(
        payload.length_m, payload.width_m, payload.height_m, payload.volume_cubic_m, allow_unknown=True
    )

    statement = select(Vehicle).where(
        Vehicle.status == VehicleStatus.available,
        Vehicle.capacity_kg >= payload.weight_kg,
    )
    if required_volume > 0:
        statement = statement.where(Vehicle.volume_cubic_m >= required_volume)
    vehicles = db.scalars(statement.order_by(Vehicle.volume_cubic_m.asc(), Vehicle.base_rate_per_km.asc())).all()

    distance = None
    if payload.origin and payload.destination:
        distance = get_known_distance(payload.origin, payload.destination)

    rows: list[VehicleMatchRead] = []
    for index, vehicle in enumerate(vehicles):
        estimated_price = round(distance * vehicle.base_rate_per_km, 2) if distance is not None else None
        rows.append(
            VehicleMatchRead(
                vehicle=VehicleRead.model_validate(vehicle),
                required_volume_cubic_m=required_volume,
                volume_spare_cubic_m=round(vehicle.volume_cubic_m - required_volume, 3),
                capacity_spare_kg=round(vehicle.capacity_kg - payload.weight_kg, 2),
                recommended=index == 0,
                estimated_distance_km=distance,
                estimated_price=estimated_price,
            )
        )
    return rows

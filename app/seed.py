from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Client, Driver, Vehicle


def seed_demo_data(db: Session) -> None:
    has_vehicle = db.scalar(select(Vehicle.id).limit(1))
    if has_vehicle is not None:
        return

    vehicles = [
        Vehicle(
            plate_number="А123ВС77",
            brand="ГАЗон Next",
            length_m=5.1,
            width_m=2.1,
            height_m=2.2,
            volume_cubic_m=23.6,
            capacity_kg=5000,
            base_rate_per_km=55,
            fuel_consumption_per_100km=18.0,
            fuel_price_per_liter=58.0,
        ),
        Vehicle(
            plate_number="М456КТ77",
            brand="MAN TGS",
            length_m=7.2,
            width_m=2.45,
            height_m=2.6,
            volume_cubic_m=45.9,
            capacity_kg=12000,
            base_rate_per_km=82,
            fuel_consumption_per_100km=28.0,
            fuel_price_per_liter=60.0,
        ),
        Vehicle(
            plate_number="О789РА77",
            brand="Volvo FH",
            length_m=13.6,
            width_m=2.45,
            height_m=2.7,
            volume_cubic_m=90.0,
            capacity_kg=22000,
            base_rate_per_km=118,
            fuel_consumption_per_100km=35.0,
            fuel_price_per_liter=60.0,
        ),
    ]
    db.add_all(vehicles)
    db.flush()

    db.add_all(
        [
            Driver(full_name="Иван Петров", license_category="C,E", experience_years=9, assigned_vehicle_id=vehicles[0].id, password="driver1"),
            Driver(full_name="Сергей Волков", license_category="C,E", experience_years=14, assigned_vehicle_id=vehicles[1].id, password="driver2"),
            Driver(full_name="Андрей Соколов", license_category="C,E", experience_years=11, assigned_vehicle_id=vehicles[2].id, password="driver3"),
        ]
    )
    db.add_all(
        [
            Client(name="ООО СеверЛогистик", contacts="+7 900 100-20-30, order@sever.example"),
            Client(name="ИП Каримов", contacts="+998 90 111-22-33"),
            Client(name="ТОО АлматыТрейд", contacts="+7 700 555-66-77"),
        ]
    )
    db.commit()

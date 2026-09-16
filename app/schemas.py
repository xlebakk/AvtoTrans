from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models import DriverStatus, OrderStatus, VehicleStatus


class VehicleBase(BaseModel):
    plate_number: str = Field(min_length=3, max_length=32)
    brand: str = Field(min_length=2, max_length=120)
    length_m: float = Field(gt=0)
    width_m: float = Field(gt=0)
    height_m: float = Field(gt=0)
    volume_cubic_m: float | None = Field(default=None, gt=0)
    capacity_kg: float = Field(gt=0)
    base_rate_per_km: float = Field(gt=0)
    fuel_consumption_per_100km: float = Field(default=25.0, gt=0)
    fuel_price_per_liter: float = Field(default=55.0, gt=0)
    status: VehicleStatus = VehicleStatus.available


class VehicleCreate(VehicleBase):
    pass


class VehicleUpdate(BaseModel):
    plate_number: str | None = Field(default=None, min_length=3, max_length=32)
    brand: str | None = Field(default=None, min_length=2, max_length=120)
    length_m: float | None = Field(default=None, gt=0)
    width_m: float | None = Field(default=None, gt=0)
    height_m: float | None = Field(default=None, gt=0)
    volume_cubic_m: float | None = Field(default=None, gt=0)
    capacity_kg: float | None = Field(default=None, gt=0)
    base_rate_per_km: float | None = Field(default=None, gt=0)
    fuel_consumption_per_100km: float | None = Field(default=None, gt=0)
    fuel_price_per_liter: float | None = Field(default=None, gt=0)
    status: VehicleStatus | None = None


class VehicleRead(VehicleBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    volume_cubic_m: float


class DriverBase(BaseModel):
    full_name: str = Field(min_length=3, max_length=160)
    license_category: str = Field(min_length=1, max_length=20)
    experience_years: int = Field(ge=0, le=70)
    assigned_vehicle_id: int | None = None
    status: DriverStatus = DriverStatus.available


class DriverCreate(DriverBase):
    pass


class DriverUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=3, max_length=160)
    license_category: str | None = Field(default=None, min_length=1, max_length=20)
    experience_years: int | None = Field(default=None, ge=0, le=70)
    assigned_vehicle_id: int | None = None
    status: DriverStatus | None = None


class DriverRead(DriverBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class ClientBase(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    contacts: str = Field(min_length=3)


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    contacts: str | None = Field(default=None, min_length=3)


class ClientRead(ClientBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class CargoRequestBase(BaseModel):
    client_id: int
    cargo_name: str | None = Field(default=None, max_length=160)
    cargo_features: str | None = None
    weight_kg: float = Field(gt=0)
    length_m: float | None = Field(default=None, gt=0)
    width_m: float | None = Field(default=None, gt=0)
    height_m: float | None = Field(default=None, gt=0)
    volume_cubic_m: float | None = Field(default=None, gt=0)
    origin: str = Field(min_length=2, max_length=160)
    origin_lat: float | None = Field(default=None, ge=-90, le=90)
    origin_lng: float | None = Field(default=None, ge=-180, le=180)
    destination: str | None = Field(default=None, max_length=160)
    destination_lat: float | None = Field(default=None, ge=-90, le=90)
    destination_lng: float | None = Field(default=None, ge=-180, le=180)


class CargoRequestCreate(CargoRequestBase):
    pass


class CargoRequestUpdate(BaseModel):
    client_id: int | None = None
    cargo_name: str | None = Field(default=None, max_length=160)
    cargo_features: str | None = None
    weight_kg: float | None = Field(default=None, gt=0)
    length_m: float | None = Field(default=None, gt=0)
    width_m: float | None = Field(default=None, gt=0)
    height_m: float | None = Field(default=None, gt=0)
    volume_cubic_m: float | None = Field(default=None, gt=0)
    origin: str | None = Field(default=None, min_length=2, max_length=160)
    origin_lat: float | None = Field(default=None, ge=-90, le=90)
    origin_lng: float | None = Field(default=None, ge=-180, le=180)
    destination: str | None = Field(default=None, max_length=160)
    destination_lat: float | None = Field(default=None, ge=-90, le=90)
    destination_lng: float | None = Field(default=None, ge=-180, le=180)


class CargoRequestRead(CargoRequestBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    volume_cubic_m: float
    created_at: datetime


class VehicleMatchRequest(BaseModel):
    weight_kg: float = Field(gt=0)
    length_m: float | None = Field(default=None, gt=0)
    width_m: float | None = Field(default=None, gt=0)
    height_m: float | None = Field(default=None, gt=0)
    volume_cubic_m: float | None = Field(default=None, gt=0)
    origin: str | None = Field(default=None, min_length=2, max_length=160)
    destination: str | None = Field(default=None, max_length=160)


class VehicleMatchRead(BaseModel):
    vehicle: VehicleRead
    required_volume_cubic_m: float
    volume_spare_cubic_m: float
    capacity_spare_kg: float
    recommended: bool
    estimated_distance_km: float | None = None
    estimated_price: float | None = None


class OrderCreate(BaseModel):
    cargo_request_id: int
    vehicle_id: int
    driver_id: int
    distance_km: float | None = Field(default=None, gt=0)
    departure_date: date | None = None
    departure_time: str | None = None  # "HH:MM"
    other_costs: float = Field(default=0.0, ge=0)


class OrderUpdate(BaseModel):
    status: OrderStatus | None = None
    departure_date: date | None = None
    departure_time: str | None = None
    delivery_date: date | None = None
    other_costs: float | None = Field(default=None, ge=0)


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cargo_request_id: int
    vehicle_id: int
    driver_id: int
    distance_km: float
    final_price: float
    fuel_cost: float
    other_costs: float
    profit: float
    status: OrderStatus
    departure_date: date | None
    delivery_date: date | None
    created_at: datetime


class TripReportRow(BaseModel):
    order_id: int
    client_name: str
    vehicle_plate: str
    driver_name: str
    origin: str
    destination: str
    distance_km: float
    final_price: float
    fuel_cost: float
    other_costs: float
    profit: float
    status: OrderStatus
    departure_date: date | None
    delivery_date: date | None


class VehicleUtilizationRow(BaseModel):
    vehicle_id: int
    plate_number: str
    brand: str
    trips_count: int
    total_distance_km: float
    total_income: float
    total_fuel_cost: float
    total_other_costs: float
    total_profit: float


class IncomeByClientRow(BaseModel):
    client_id: int
    client_name: str
    orders_count: int
    total_income: float

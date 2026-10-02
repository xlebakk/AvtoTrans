from datetime import date
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import CargoRequest, Client, Driver, DriverStatus, Order, Vehicle
from app.schemas import CargoRequestCreate, OrderCreate, VehicleMatchRequest
from app.services.common import calculate_volume, get_or_404
from app.services.matching import find_matching_vehicles
from app.services.orders import complete_order, create_order, start_order
from app.services.reports import income_by_clients, monthly_stats, trips_for_period, vehicle_utilization
from app.ui_config import CURRENCIES, get_currency_info, load_ui_config, normalize_sections_order, save_ui_config

router = APIRouter(tags=["web"])
templates = Jinja2Templates(directory="app/templates")

ADMIN_PASSWORD = "admin123"


def is_admin(request: Request) -> bool:
    return request.cookies.get("admin_mode") == "1"


def require_admin(request: Request) -> RedirectResponse | None:
    if is_admin(request):
        return None
    return RedirectResponse("/login", status_code=303)


def base_context(request: Request, title: str) -> dict:
    ui_config = load_ui_config()
    dae_model = Path("app/static/models/model.dae")
    glb_model = Path("app/static/models/truck.glb")
    truck_model_url = None
    if ui_config["model_mode"] == "dae" and dae_model.exists():
        truck_model_url = "/static/models/model.dae"
    elif ui_config["model_mode"] == "glb" and glb_model.exists():
        truck_model_url = "/static/models/truck.glb"
    currency = get_currency_info(ui_config)
    return {
        "is_admin": is_admin(request),
        "title": title,
        "error": None,
        "truck_model_url": truck_model_url,
        "show_truck_viewer": ui_config["model_mode"] != "none",
        "ui_config": ui_config,
        "currency_symbol": currency["symbol"],
        "currency_code": currency["code"],
        "currency_name": currency["name"],
    }


def admin_context(request: Request, db: Session, title: str) -> dict:
    vehicles = list(db.scalars(select(Vehicle).order_by(Vehicle.volume_cubic_m.asc())))
    drivers = list(db.scalars(select(Driver).order_by(Driver.full_name.asc())))
    clients = list(db.scalars(select(Client).order_by(Client.name.asc())))
    cargo_requests = list(db.scalars(select(CargoRequest).order_by(CargoRequest.created_at.desc())))
    orders = list(db.scalars(select(Order).order_by(Order.created_at.desc())))
    all_trips = trips_for_period(db, None, None)
    total_income = sum(t.final_price for t in all_trips)
    total_fuel = sum(t.fuel_cost for t in all_trips)
    total_other = sum(t.other_costs for t in all_trips)
    total_profit = sum(t.profit for t in all_trips)
    return {
        **base_context(request, title),
        "vehicles": vehicles,
        "drivers": drivers,
        "clients": clients,
        "cargo_requests": cargo_requests,
        "orders": orders,
        "available_drivers": [driver for driver in drivers if driver.status == DriverStatus.available],
        "utilization": vehicle_utilization(db),
        "income_clients": income_by_clients(db),
        "trips": all_trips,
        "total_income": total_income,
        "total_fuel": total_fuel,
        "total_other": total_other,
        "total_profit": total_profit,
    }

@router.get("/", response_class=HTMLResponse)
def home(request: Request) -> Response:
    if is_admin(request):
        return RedirectResponse("/admin", status_code=302)
    return RedirectResponse("/login", status_code=302)

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request) -> HTMLResponse:
    context = base_context(request, "Вход в систему")
    err = request.query_params.get("error")
    if err:
        context["error"] = err   # "driver" | "1" | anything
    return templates.TemplateResponse(request, "login.html", context)


@router.post("/login")
def login(password: str = Form(...)) -> RedirectResponse:
    if password != ADMIN_PASSWORD:
        response = RedirectResponse("/login?error=1", status_code=303)
        response.delete_cookie("admin_mode")
        return response
    response = RedirectResponse("/admin", status_code=303)
    response.set_cookie("admin_mode", "1", httponly=True, samesite="lax")
    return response


@router.post("/logout")
def logout() -> RedirectResponse:
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie("admin_mode")
    return response

@router.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request, db: Session = Depends(get_db)) -> Response:
    redirect = require_admin(request)
    if redirect:
        return redirect
    return templates.TemplateResponse(request, "admin_dashboard.html", admin_context(request, db, "Панель управления"))

@router.get("/admin/orders-intake", response_class=HTMLResponse)
def admin_orders_intake(request: Request, db: Session = Depends(get_db)) -> Response:
    redirect = require_admin(request)
    if redirect:
        return redirect
    return templates.TemplateResponse(request, "admin_requests.html", admin_context(request, db, "Заказы клиентов"))


@router.get("/admin/orders-intake/new", response_class=HTMLResponse)
def admin_orders_intake_new(request: Request, db: Session = Depends(get_db)) -> Response:
    redirect = require_admin(request)
    if redirect:
        return redirect
    return templates.TemplateResponse(request, "admin_new_order.html", admin_context(request, db, "Новый заказ"))


@router.post("/ui/cargo-requests")
def create_cargo_request_ui(
    request: Request,
    client_id: int = Form(...),
    cargo_name: str | None = Form(default=None),
    cargo_features: str | None = Form(default=None),
    weight_kg: float = Form(...),
    length_m: float | None = Form(default=None),
    width_m: float | None = Form(default=None),
    height_m: float | None = Form(default=None),
    volume_cubic_m: float | None = Form(default=None),
    origin: str = Form(...),
    destination: str | None = Form(default=None),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    redirect = require_admin(request)
    if redirect:
        return redirect
    cargo_payload = CargoRequestCreate(
        client_id=client_id,
        cargo_name=cargo_name,
        cargo_features=cargo_features,
        weight_kg=weight_kg,
        length_m=length_m,
        width_m=width_m,
        height_m=height_m,
        volume_cubic_m=volume_cubic_m,
        origin=origin,
        destination=destination or "",
    )
    cargo_request = CargoRequest(
        **cargo_payload.model_dump(exclude={"volume_cubic_m"}),
        volume_cubic_m=calculate_volume(length_m, width_m, height_m, volume_cubic_m, allow_unknown=True),
    )
    db.add(cargo_request)
    db.commit()
    db.refresh(cargo_request)
    return RedirectResponse(f"/admin/orders-intake/{cargo_request.id}/match", status_code=303)


@router.get("/admin/orders-intake/{request_id}/match", response_class=HTMLResponse)
def admin_request_match(
    request_id: int, request: Request, db: Session = Depends(get_db)
) -> Response:
    redirect = require_admin(request)
    if redirect:
        return redirect
    cargo_request = get_or_404(db, CargoRequest, request_id, "Заявка")
    matches = find_matching_vehicles(
        db,
        VehicleMatchRequest(
            weight_kg=cargo_request.weight_kg,
            volume_cubic_m=cargo_request.volume_cubic_m or None,
            origin=cargo_request.origin,
            destination=cargo_request.destination or None,
        ),
    )
    return templates.TemplateResponse(
        request,
        "admin_request_match.html",
        {
            **admin_context(request, db, "Назначение рейса"),
            "cargo_request": cargo_request,
            "matches": matches,
            "error": request.query_params.get("error"),
        },
    )

@router.get("/admin/trips", response_class=HTMLResponse)
def admin_trips(request: Request, db: Session = Depends(get_db)) -> Response:
    redirect = require_admin(request)
    if redirect:
        return redirect
    return templates.TemplateResponse(request, "admin_orders.html", admin_context(request, db, "Рейсы"))


@router.get("/admin/trips/{order_id}", response_class=HTMLResponse)
def admin_trip_detail(order_id: int, request: Request, db: Session = Depends(get_db)) -> Response:
    redirect = require_admin(request)
    if redirect:
        return redirect
    order = get_or_404(db, Order, order_id, "Рейс")
    ctx = admin_context(request, db, f"Рейс #{order_id}")
    ctx["order"] = order
    return templates.TemplateResponse(request, "admin_trip_detail.html", ctx)


@router.post("/ui/admin/driver-password/{driver_id}")
def admin_set_driver_password(
    driver_id: int,
    request: Request,
    password: str = Form(...),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    """Задать/сбросить пароль водителя для входа в портал."""
    redirect = require_admin(request)
    if redirect:
        return redirect
    from app.models import Driver as DriverModel
    driver = db.get(DriverModel, driver_id)
    if driver:
        driver.password = password
        db.commit()
    return RedirectResponse(f"/admin/drivers", status_code=303)

@router.get("/admin/fleet", response_class=HTMLResponse)
def admin_fleet(request: Request, db: Session = Depends(get_db)) -> Response:
    redirect = require_admin(request)
    if redirect:
        return redirect
    return templates.TemplateResponse(request, "admin_fleet.html", admin_context(request, db, "Грузовики"))

@router.get("/admin/drivers", response_class=HTMLResponse)
def admin_drivers(request: Request, db: Session = Depends(get_db)) -> Response:
    redirect = require_admin(request)
    if redirect:
        return redirect
    return templates.TemplateResponse(request, "admin_drivers.html", admin_context(request, db, "Водители"))

@router.get("/admin/clients", response_class=HTMLResponse)
def admin_clients(request: Request, db: Session = Depends(get_db)) -> Response:
    redirect = require_admin(request)
    if redirect:
        return redirect
    return templates.TemplateResponse(request, "admin_clients.html", admin_context(request, db, "Клиенты"))

@router.get("/admin/reports", response_class=HTMLResponse)
def admin_reports(request: Request, month: str | None = None, db: Session = Depends(get_db)) -> Response:
    redirect = require_admin(request)
    if redirect:
        return redirect
    ctx = admin_context(request, db, "Отчёты")
    stats = monthly_stats(db)
    ctx["monthly_stats"] = stats
    ctx["selected_month"] = month
    if month and len(month) == 7:
        try:
            y, m = map(int, month.split("-"))
            ctx["filtered_trips"] = [
                t for t in ctx["trips"]
                if t.departure_date and t.departure_date.year == y and t.departure_date.month == m
            ]
        except (ValueError, AttributeError):
            ctx["filtered_trips"] = ctx["trips"]
    else:
        ctx["filtered_trips"] = ctx["trips"]
    return templates.TemplateResponse(request, "admin_reports.html", ctx)

@router.post("/ui/clients")
def create_client_ui(
    request: Request,
    name: str = Form(...),
    contacts: str = Form(...),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    redirect = require_admin(request)
    if redirect:
        return redirect
    db.add(Client(name=name, contacts=contacts))
    db.commit()
    return RedirectResponse("/admin/clients", status_code=303)


@router.post("/ui/vehicles")
def create_vehicle_ui(
    request: Request,
    plate_number: str = Form(...),
    brand: str = Form(...),
    length_m: float = Form(...),
    width_m: float = Form(...),
    height_m: float = Form(...),
    capacity_kg: float = Form(...),
    base_rate_per_km: float = Form(...),
    fuel_consumption_per_100km: float = Form(default=25.0),
    fuel_price_per_liter: float = Form(default=55.0),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    redirect = require_admin(request)
    if redirect:
        return redirect
    db.add(
        Vehicle(
            plate_number=plate_number,
            brand=brand,
            length_m=length_m,
            width_m=width_m,
            height_m=height_m,
            volume_cubic_m=calculate_volume(length_m, width_m, height_m, None),
            capacity_kg=capacity_kg,
            base_rate_per_km=base_rate_per_km,
            fuel_consumption_per_100km=fuel_consumption_per_100km,
            fuel_price_per_liter=fuel_price_per_liter,
        )
    )
    db.commit()
    return RedirectResponse("/admin/fleet", status_code=303)


@router.post("/ui/drivers")
def create_driver_ui(
    request: Request,
    full_name: str = Form(...),
    license_category: str = Form(...),
    license_category_custom: str | None = Form(default=None),
    experience_years: int = Form(...),
    assigned_vehicle_id: int | None = Form(default=None),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    redirect = require_admin(request)
    if redirect:
        return redirect
    selected_category = license_category_custom if license_category == "__custom__" else license_category
    db.add(
        Driver(
            full_name=full_name,
            license_category=selected_category or "C,E",
            experience_years=experience_years,
            assigned_vehicle_id=assigned_vehicle_id,
        )
    )
    db.commit()
    return RedirectResponse("/admin/drivers", status_code=303)


@router.post("/ui/orders")
def create_order_ui(
    request: Request,
    cargo_request_id: int = Form(...),
    vehicle_id: int = Form(...),
    driver_id: int = Form(...),
    distance_km: float | None = Form(default=None),
    departure_date: date | None = Form(default=None),
    departure_time: str | None = Form(default=None),
    other_costs: float = Form(default=0.0),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    redirect = require_admin(request)
    if redirect:
        return redirect
    try:
        create_order(
            db,
            OrderCreate(
                cargo_request_id=cargo_request_id,
                vehicle_id=vehicle_id,
                driver_id=driver_id,
                distance_km=distance_km,
                departure_date=departure_date,
                departure_time=departure_time or None,
                other_costs=other_costs,
            ),
        )
    except HTTPException as exc:
        detail = quote(str(exc.detail))
        return RedirectResponse(f"/admin/orders-intake/{cargo_request_id}/match?error={detail}", status_code=303)
    return RedirectResponse("/admin/trips", status_code=303)


@router.post("/ui/orders/{order_id}/start")
def start_order_ui(order_id: int, request: Request, db: Session = Depends(get_db)) -> RedirectResponse:
    redirect = require_admin(request)
    if redirect:
        return redirect
    start_order(db, order_id)
    return RedirectResponse("/admin/trips", status_code=303)


@router.post("/ui/orders/{order_id}/complete")
def complete_order_ui(order_id: int, request: Request, db: Session = Depends(get_db)) -> RedirectResponse:
    redirect = require_admin(request)
    if redirect:
        return redirect
    complete_order(db, order_id)
    return RedirectResponse("/admin/trips", status_code=303)


@router.get("/admin/settings", response_class=HTMLResponse)
def settings_page(request: Request) -> Response:
    redirect = require_admin(request)
    if redirect:
        return redirect
    cfg = load_ui_config()
    ctx = base_context(request, "Настройки")
    ctx["cfg"] = cfg
    ctx["currencies"] = CURRENCIES
    ctx["saved"] = request.query_params.get("saved") == "1"
    return templates.TemplateResponse(request, "settings.html", ctx)


@router.post("/admin/settings")
def settings_save(
    request: Request,
    currency: str = Form(default="TJS"),
    client_title: str = Form(default="АвтоТранс"),
    client_badge: str = Form(default="Автоматизация транспортной компании"),
    model_mode: str = Form(default="none"),
) -> RedirectResponse:
    redirect = require_admin(request)
    if redirect:
        return redirect
    from app.ui_config import CURRENCIES, normalize_sections_order
    cfg = load_ui_config()
    cfg["currency"] = currency if currency in CURRENCIES else "TJS"
    cfg["client_title"] = client_title.strip() or "АвтоТранс"
    cfg["client_badge"] = client_badge.strip()
    cfg["model_mode"] = model_mode if model_mode in ("dae", "glb", "none") else "none"
    save_ui_config(cfg)
    return RedirectResponse("/admin/settings?saved=1", status_code=303)

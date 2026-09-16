"""
Портал водителя — маршруты:
  GET  /driver/login          — страница входа
  POST /driver/login          — аутентификация (ID + пароль)
  POST /driver/logout         — выход
  GET  /driver                — дашборд: активный заказ + кнопки статуса
  GET  /driver/history        — история рейсов водителя
  POST /ui/driver/status/{order_id}/{status}  — изменить статус рейса
  POST /api/driver/location   — обновить GPS (JSON: {lat, lon})
  GET  /api/driver/chat/{order_id}  — сообщения чата (JSON)
  POST /api/driver/chat/{order_id}  — отправить сообщение
  GET  /api/admin/chat/{order_id}   — чат со стороны admin
  POST /api/admin/chat/{order_id}   — ответить водителю
"""
from datetime import datetime

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ChatMessage, Driver, DriverStatus, Order, OrderStatus, VehicleStatus

router = APIRouter(tags=["driver"])
templates = Jinja2Templates(directory="app/templates")

ACTIVE_STATUSES = (OrderStatus.assigned, OrderStatus.arrived, OrderStatus.in_transit)


# ─── Auth helpers ──────────────────────────────────────────────────────────────

def get_driver_id(request: Request) -> int | None:
    try:
        return int(request.cookies.get("driver_id", ""))
    except (TypeError, ValueError):
        return None


def require_driver(request: Request, db: Session) -> Driver | RedirectResponse:
    did = get_driver_id(request)
    if did is None:
        return RedirectResponse("/driver/login", status_code=303)
    driver = db.get(Driver, did)
    if driver is None:
        return RedirectResponse("/driver/login", status_code=303)
    return driver


# ─── Login ─────────────────────────────────────────────────────────────────────

@router.get("/driver/login", response_class=HTMLResponse)
def driver_login_page(request: Request, error: str | None = None) -> Response:
    # Redirect to unified login page
    return RedirectResponse("/login", status_code=302)


@router.post("/driver/login")
def driver_login(
    request: Request,
    driver_id: int = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    driver = db.get(Driver, driver_id)
    if driver is None or driver.password != password:
        return RedirectResponse("/login?error=driver", status_code=303)
    resp = RedirectResponse("/driver", status_code=303)
    resp.set_cookie("driver_id", str(driver.id), httponly=True, samesite="lax", max_age=86400 * 30)
    return resp


@router.post("/driver/logout")
def driver_logout() -> RedirectResponse:
    resp = RedirectResponse("/driver/login", status_code=303)
    resp.delete_cookie("driver_id")
    return resp


# ─── Dashboard ─────────────────────────────────────────────────────────────────

@router.get("/driver", response_class=HTMLResponse)
def driver_dashboard(request: Request, db: Session = Depends(get_db)) -> Response:
    result = require_driver(request, db)
    if isinstance(result, RedirectResponse):
        return result
    driver = result

    # Активный рейс
    active_order = db.scalar(
        select(Order)
        .where(Order.driver_id == driver.id, Order.status.in_(ACTIVE_STATUSES))
        .limit(1)
    )

    # Статистика водителя — всегда загружаем
    all_orders = db.scalars(
        select(Order)
        .where(Order.driver_id == driver.id)
        .order_by(Order.created_at.desc())
    ).all()

    delivered = [o for o in all_orders if o.status.value == "доставлен"]
    total_km   = sum(o.distance_km for o in all_orders)
    total_fuel = sum(o.fuel_cost   for o in all_orders)
    recent     = all_orders[:5]   # последние 5 рейсов

    return templates.TemplateResponse(request, "driver_dashboard.html", {
        "title": f"Портал водителя — {driver.full_name}",
        "driver": driver,
        "active_order": active_order,
        "stat_trips": len(delivered),
        "stat_km": round(total_km),
        "stat_fuel": round(total_fuel),
        "recent_orders": recent,
    })


# ─── История ───────────────────────────────────────────────────────────────────

@router.get("/driver/history", response_class=HTMLResponse)
def driver_history(request: Request, db: Session = Depends(get_db)) -> Response:
    result = require_driver(request, db)
    if isinstance(result, RedirectResponse):
        return result
    driver = result

    orders = db.scalars(
        select(Order)
        .where(Order.driver_id == driver.id)
        .order_by(Order.created_at.desc())
    ).all()

    total_km    = sum(o.distance_km for o in orders)
    total_fuel  = sum(o.fuel_cost   for o in orders)
    total_trips = len(orders)

    return templates.TemplateResponse(request, "driver_history.html", {
        "title": "Моя история рейсов",
        "driver": driver,
        "orders": orders,
        "total_km": total_km,
        "total_fuel": total_fuel,
        "total_trips": total_trips,
    })


# ─── Изменить статус рейса ─────────────────────────────────────────────────────

STATUS_MAP = {
    "arrived":    OrderStatus.arrived,
    "in_transit": OrderStatus.in_transit,
    "delivered":  OrderStatus.delivered,
}

@router.post("/ui/driver/status/{order_id}/{new_status}")
def driver_update_status(
    order_id: int,
    new_status: str,
    request: Request,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    result = require_driver(request, db)
    if isinstance(result, RedirectResponse):
        return result
    driver = result

    order = db.get(Order, order_id)
    if order is None or order.driver_id != driver.id:
        return RedirectResponse("/driver", status_code=303)

    mapped = STATUS_MAP.get(new_status)
    if mapped:
        order.status = mapped
        if mapped == OrderStatus.in_transit:
            order.vehicle.status = VehicleStatus.in_trip
            driver.status = DriverStatus.in_trip
            if order.departure_date is None:
                from datetime import date
                order.departure_date = date.today()
        elif mapped == OrderStatus.delivered:
            from datetime import date
            order.delivery_date = date.today()
            order.vehicle.status = VehicleStatus.available
            driver.status = DriverStatus.available
        db.commit()

    return RedirectResponse("/driver", status_code=303)


# ─── GPS location update ───────────────────────────────────────────────────────

@router.post("/api/driver/location")
async def driver_update_location(request: Request, db: Session = Depends(get_db)) -> JSONResponse:
    did = get_driver_id(request)
    if did is None:
        return JSONResponse({"ok": False, "error": "not authenticated"}, status_code=401)
    driver = db.get(Driver, did)
    if driver is None:
        return JSONResponse({"ok": False, "error": "driver not found"}, status_code=404)

    body = await request.json()
    driver.last_lat  = body.get("lat")
    driver.last_lon  = body.get("lon")
    driver.last_seen = datetime.utcnow()
    db.commit()
    return JSONResponse({"ok": True})


# ─── Driver location for admin ─────────────────────────────────────────────────

@router.get("/api/admin/driver-location/{driver_id}")
def admin_get_driver_location(driver_id: int, db: Session = Depends(get_db)) -> JSONResponse:
    driver = db.get(Driver, driver_id)
    if driver is None:
        return JSONResponse({"ok": False}, status_code=404)
    return JSONResponse({
        "ok": True,
        "lat": driver.last_lat,
        "lon": driver.last_lon,
        "last_seen": driver.last_seen.isoformat() if driver.last_seen else None,
        "name": driver.full_name,
    })


# ─── Chat: driver side ─────────────────────────────────────────────────────────

@router.get("/api/driver/chat/{order_id}")
def driver_get_chat(order_id: int, request: Request, db: Session = Depends(get_db)) -> JSONResponse:
    did = get_driver_id(request)
    if did is None:
        return JSONResponse([], status_code=401)
    msgs = db.scalars(
        select(ChatMessage)
        .where(ChatMessage.order_id == order_id, ChatMessage.driver_id == did)
        .order_by(ChatMessage.created_at)
    ).all()
    # Mark admin messages as read
    for m in msgs:
        if m.sender == "admin" and not m.is_read:
            m.is_read = True
    db.commit()
    return JSONResponse([{
        "id": m.id, "sender": m.sender, "text": m.text,
        "created_at": m.created_at.strftime("%H:%M"),
    } for m in msgs])


@router.post("/api/driver/chat/{order_id}")
async def driver_send_message(order_id: int, request: Request, db: Session = Depends(get_db)) -> JSONResponse:
    did = get_driver_id(request)
    if did is None:
        return JSONResponse({"ok": False}, status_code=401)
    body = await request.json()
    text = (body.get("text") or "").strip()
    if not text:
        return JSONResponse({"ok": False, "error": "empty"}, status_code=400)
    msg = ChatMessage(order_id=order_id, driver_id=did, sender="driver", text=text)
    db.add(msg)
    db.commit()
    return JSONResponse({"ok": True, "id": msg.id})


# ─── Chat: admin side ──────────────────────────────────────────────────────────

@router.get("/api/admin/chat/{order_id}")
def admin_get_chat(order_id: int, db: Session = Depends(get_db)) -> JSONResponse:
    order = db.get(Order, order_id)
    if order is None:
        return JSONResponse([], status_code=404)
    msgs = db.scalars(
        select(ChatMessage)
        .where(ChatMessage.order_id == order_id)
        .order_by(ChatMessage.created_at)
    ).all()
    # Mark driver messages as read by admin
    for m in msgs:
        if m.sender == "driver" and not m.is_read:
            m.is_read = True
    db.commit()
    return JSONResponse([{
        "id": m.id, "sender": m.sender, "text": m.text,
        "created_at": m.created_at.strftime("%H:%M"),
        "is_read": m.is_read,
    } for m in msgs])


@router.post("/api/admin/chat/{order_id}")
async def admin_send_message(order_id: int, request: Request, db: Session = Depends(get_db)) -> JSONResponse:
    order = db.get(Order, order_id)
    if order is None:
        return JSONResponse({"ok": False}, status_code=404)
    body = await request.json()
    text = (body.get("text") or "").strip()
    if not text:
        return JSONResponse({"ok": False, "error": "empty"}, status_code=400)
    msg = ChatMessage(order_id=order_id, driver_id=order.driver_id, sender="admin", text=text)
    db.add(msg)
    db.commit()
    return JSONResponse({"ok": True, "id": msg.id})


# ─── Unread count for admin notification ──────────────────────────────────────

@router.get("/api/admin/chat-unread")
def admin_unread_count(db: Session = Depends(get_db)) -> JSONResponse:
    msgs = db.scalars(
        select(ChatMessage).where(ChatMessage.sender == "driver", ChatMessage.is_read == False)
    ).all()
    return JSONResponse({"unread": len(msgs)})


# ─── General Chat (без привязки к заказу) ──────────────────────────────────────

@router.get("/api/driver/chat/general")
def driver_get_general_chat(request: Request, db: Session = Depends(get_db)) -> JSONResponse:
    """Общий чат водителя с поддержкой — без привязки к рейсу."""
    did = get_driver_id(request)
    if did is None:
        return JSONResponse([], status_code=401)
    msgs = db.scalars(
        select(ChatMessage)
        .where(ChatMessage.driver_id == did, ChatMessage.order_id == None)
        .order_by(ChatMessage.created_at)
    ).all()
    for m in msgs:
        if m.sender == "admin" and not m.is_read:
            m.is_read = True
    db.commit()
    return JSONResponse([{
        "id": m.id, "sender": m.sender, "text": m.text,
        "created_at": m.created_at.strftime("%H:%M"),
    } for m in msgs])


@router.post("/api/driver/chat/general")
async def driver_send_general(request: Request, db: Session = Depends(get_db)) -> JSONResponse:
    did = get_driver_id(request)
    if did is None:
        return JSONResponse({"ok": False}, status_code=401)
    body = await request.json()
    text = (body.get("text") or "").strip()
    if not text:
        return JSONResponse({"ok": False, "error": "empty"}, status_code=400)
    msg = ChatMessage(order_id=None, driver_id=did, sender="driver", text=text)
    db.add(msg)
    db.commit()
    return JSONResponse({"ok": True, "id": msg.id})


@router.get("/api/admin/chat/general/{driver_id}")
def admin_get_general_chat(driver_id: int, db: Session = Depends(get_db)) -> JSONResponse:
    msgs = db.scalars(
        select(ChatMessage)
        .where(ChatMessage.driver_id == driver_id, ChatMessage.order_id == None)
        .order_by(ChatMessage.created_at)
    ).all()
    for m in msgs:
        if m.sender == "driver" and not m.is_read:
            m.is_read = True
    db.commit()
    return JSONResponse([{
        "id": m.id, "sender": m.sender, "text": m.text,
        "created_at": m.created_at.strftime("%H:%M"),
        "is_read": m.is_read,
    } for m in msgs])


@router.post("/api/admin/chat/general/{driver_id}")
async def admin_send_general(driver_id: int, request: Request, db: Session = Depends(get_db)) -> JSONResponse:
    driver = db.get(Driver, driver_id)
    if driver is None:
        return JSONResponse({"ok": False}, status_code=404)
    body = await request.json()
    text = (body.get("text") or "").strip()
    if not text:
        return JSONResponse({"ok": False, "error": "empty"}, status_code=400)
    msg = ChatMessage(order_id=None, driver_id=driver_id, sender="admin", text=text)
    db.add(msg)
    db.commit()
    return JSONResponse({"ok": True, "id": msg.id})


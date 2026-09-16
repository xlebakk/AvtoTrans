from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Order
from app.schemas import OrderCreate, OrderRead, OrderUpdate
from app.services.common import get_or_404
from app.services.orders import complete_order, create_order, start_order

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.get("", response_model=list[OrderRead])
def list_orders(db: Session = Depends(get_db)) -> list[Order]:
    return list(db.scalars(select(Order).order_by(Order.created_at.desc())))


@router.post("", response_model=OrderRead, status_code=201)
def create_order_endpoint(payload: OrderCreate, db: Session = Depends(get_db)) -> Order:
    return create_order(db, payload)


@router.get("/{order_id}", response_model=OrderRead)
def get_order(order_id: int, db: Session = Depends(get_db)) -> Order:
    return get_or_404(db, Order, order_id, "Заказ")


@router.put("/{order_id}", response_model=OrderRead)
def update_order(order_id: int, payload: OrderUpdate, db: Session = Depends(get_db)) -> Order:
    order = get_or_404(db, Order, order_id, "Заказ")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(order, field, value)
    db.commit()
    db.refresh(order)
    return order


@router.post("/{order_id}/start", response_model=OrderRead)
def start_order_endpoint(order_id: int, db: Session = Depends(get_db)) -> Order:
    return start_order(db, order_id)


@router.post("/{order_id}/complete", response_model=OrderRead)
def complete_order_endpoint(order_id: int, db: Session = Depends(get_db)) -> Order:
    return complete_order(db, order_id)


@router.delete("/{order_id}", status_code=204)
def delete_order(order_id: int, db: Session = Depends(get_db)) -> None:
    order = get_or_404(db, Order, order_id, "Заказ")
    db.delete(order)
    db.commit()


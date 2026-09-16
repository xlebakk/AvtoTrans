from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Client
from app.schemas import ClientCreate, ClientRead, ClientUpdate
from app.services.common import get_or_404

router = APIRouter(prefix="/api/clients", tags=["clients"])


@router.get("", response_model=list[ClientRead])
def list_clients(db: Session = Depends(get_db)) -> list[Client]:
    return list(db.scalars(select(Client).order_by(Client.id)))


@router.post("", response_model=ClientRead, status_code=201)
def create_client(payload: ClientCreate, db: Session = Depends(get_db)) -> Client:
    client = Client(**payload.model_dump())
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@router.get("/{client_id}", response_model=ClientRead)
def get_client(client_id: int, db: Session = Depends(get_db)) -> Client:
    return get_or_404(db, Client, client_id, "Клиент")


@router.put("/{client_id}", response_model=ClientRead)
def update_client(client_id: int, payload: ClientUpdate, db: Session = Depends(get_db)) -> Client:
    client = get_or_404(db, Client, client_id, "Клиент")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(client, field, value)
    db.commit()
    db.refresh(client)
    return client


@router.delete("/{client_id}", status_code=204)
def delete_client(client_id: int, db: Session = Depends(get_db)) -> None:
    client = get_or_404(db, Client, client_id, "Клиент")
    db.delete(client)
    db.commit()


from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.database import get_session
from app.core.deps import get_current_user
from app.modules.identity.domain import UserEntity
from app.modules.inventory.repository import SqlInventoryRepository
from app.modules.inventory.schemas import InventoryLotResponse, InventoryLotUpdate


router = APIRouter(prefix="/api/inventory-lots", tags=["inventory"])


@router.get("", response_model=list[InventoryLotResponse])
def list_inventory_lots(
    current_user: UserEntity = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return SqlInventoryRepository(session).list_lots(current_user.id)


@router.patch("/{lot_id}", response_model=InventoryLotResponse)
def update_inventory_lot(
    lot_id: int,
    data: InventoryLotUpdate,
    current_user: UserEntity = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    repo = SqlInventoryRepository(session)
    result = repo.update_lot(current_user.id, lot_id, data.model_dump(exclude_none=True))
    session.commit()
    return result

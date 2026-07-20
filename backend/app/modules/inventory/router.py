from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.deps import get_current_user
from app.dependencies import get_list_inventory_lots_use_case, get_update_inventory_lot_use_case
from app.modules.identity.domain import UserEntity
from app.modules.inventory.schemas import InventoryLotResponse, InventoryLotUpdate
from app.modules.inventory.use_cases import ListInventoryLotsUseCase, UpdateInventoryLotUseCase


router = APIRouter(prefix="/api/inventory-lots", tags=["inventory"])


@router.get("", response_model=list[InventoryLotResponse])
def list_inventory_lots(
    current_user: UserEntity = Depends(get_current_user),
    use_case: ListInventoryLotsUseCase = Depends(get_list_inventory_lots_use_case),
):
    return use_case.execute(current_user.id)


@router.patch("/{lot_id}", response_model=InventoryLotResponse)
def update_inventory_lot(
    lot_id: int,
    data: InventoryLotUpdate,
    current_user: UserEntity = Depends(get_current_user),
    use_case: UpdateInventoryLotUseCase = Depends(get_update_inventory_lot_use_case),
):
    return use_case.execute(
        current_user.id,
        lot_id,
        data.model_dump(exclude_none=True),
    )

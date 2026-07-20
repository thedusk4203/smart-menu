from __future__ import annotations

from typing import Any

from app.modules.inventory.ports import InventoryRepositoryPort, InventoryUnitOfWorkPort


class ListInventoryLotsUseCase:
    def __init__(self, repository: InventoryRepositoryPort) -> None:
        self._repository = repository

    def execute(self, user_id: int) -> list[dict[str, Any]]:
        return self._repository.list_lots(user_id)


class UpdateInventoryLotUseCase:
    def __init__(self, unit_of_work: InventoryUnitOfWorkPort) -> None:
        self._unit_of_work = unit_of_work

    def execute(self, user_id: int, lot_id: int, changes: dict[str, Any]) -> dict[str, Any]:
        try:
            result = self._unit_of_work.inventory.update_lot(user_id, lot_id, changes)
            self._unit_of_work.commit()
            return result
        except Exception:
            self._unit_of_work.rollback()
            raise

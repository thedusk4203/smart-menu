from __future__ import annotations

import pytest

from app.modules.inventory.use_cases import ListInventoryLotsUseCase, UpdateInventoryLotUseCase


class _InventoryRepository:
    def __init__(self) -> None:
        self.updated: tuple[int, int, dict] | None = None
        self.error: Exception | None = None

    def list_lots(self, user_id: int) -> list[dict]:
        return [{"id": 1, "user_id": user_id}]

    def update_lot(self, user_id: int, lot_id: int, changes: dict) -> dict:
        if self.error is not None:
            raise self.error
        self.updated = (user_id, lot_id, changes)
        return {"id": lot_id, **changes}


class _InventoryUnitOfWork:
    def __init__(self, repository: _InventoryRepository) -> None:
        self.inventory = repository
        self.commits = 0
        self.rollbacks = 0

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


def test_list_inventory_lots_delegates_to_repository() -> None:
    repository = _InventoryRepository()

    result = ListInventoryLotsUseCase(repository).execute(7)

    assert result == [{"id": 1, "user_id": 7}]


def test_update_inventory_lot_commits_once() -> None:
    repository = _InventoryRepository()
    unit_of_work = _InventoryUnitOfWork(repository)

    result = UpdateInventoryLotUseCase(unit_of_work).execute(7, 3, {"status": "discarded"})

    assert result == {"id": 3, "status": "discarded"}
    assert repository.updated == (7, 3, {"status": "discarded"})
    assert unit_of_work.commits == 1
    assert unit_of_work.rollbacks == 0


def test_update_inventory_lot_rolls_back_on_error() -> None:
    repository = _InventoryRepository()
    repository.error = RuntimeError("database failed")
    unit_of_work = _InventoryUnitOfWork(repository)

    with pytest.raises(RuntimeError, match="database failed"):
        UpdateInventoryLotUseCase(unit_of_work).execute(7, 3, {"status": "discarded"})

    assert unit_of_work.commits == 0
    assert unit_of_work.rollbacks == 1


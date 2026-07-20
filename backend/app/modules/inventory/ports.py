from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import Any

from app.modules.inventory.domain import InventoryLotSnapshot, PersistedPlanInventory


class InventoryRepositoryPort(ABC):
    @abstractmethod
    def snapshots_for_plan(
        self, user_id: int, start_date: date, end_date: date
    ) -> tuple[tuple[InventoryLotSnapshot, ...], str]: ...

    @abstractmethod
    def verify_fingerprint(
        self, user_id: int, start_date: date, end_date: date, expected: str | None
    ) -> None: ...

    @abstractmethod
    def reserve_inputs(self, plan: PersistedPlanInventory) -> None: ...

    @abstractmethod
    def create_ending_lots(self, plan: PersistedPlanInventory) -> None: ...

    @abstractmethod
    def release_plan(self, plan_id: int) -> None: ...

    @abstractmethod
    def list_lots(self, user_id: int) -> list[dict[str, Any]]: ...

    @abstractmethod
    def update_lot(
        self, user_id: int, lot_id: int, changes: dict[str, Any]
    ) -> dict[str, Any]: ...


class InventoryUnitOfWorkPort(ABC):
    @property
    @abstractmethod
    def inventory(self) -> InventoryRepositoryPort: ...

    @abstractmethod
    def commit(self) -> None: ...

    @abstractmethod
    def rollback(self) -> None: ...

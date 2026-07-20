from __future__ import annotations

from sqlmodel import Session

from app.modules.inventory.ports import InventoryRepositoryPort, InventoryUnitOfWorkPort
from app.modules.inventory.repository import SqlInventoryRepository


class SqlInventoryUnitOfWork(InventoryUnitOfWorkPort):
    def __init__(self, session: Session) -> None:
        self._session = session
        self._inventory = SqlInventoryRepository(session)

    @property
    def inventory(self) -> InventoryRepositoryPort:
        return self._inventory

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()

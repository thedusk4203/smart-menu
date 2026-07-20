from __future__ import annotations

from sqlmodel import Session

from app.modules.inventory.ports import InventoryRepositoryPort
from app.modules.inventory.repository import SqlInventoryRepository
from app.modules.meal_planning.ports import MealPlanRepositoryPort, MealPlanUnitOfWorkPort
from app.modules.meal_planning.repository import SqlMealPlanRepository


class SqlMealPlanUnitOfWork(MealPlanUnitOfWorkPort):
    """Một transaction dùng chung cho meal plan và inventory ledger."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._plans = SqlMealPlanRepository(session)
        self._inventory = SqlInventoryRepository(session)

    @property
    def plans(self) -> MealPlanRepositoryPort:
        return self._plans

    @property
    def inventory(self) -> InventoryRepositoryPort:
        return self._inventory

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()

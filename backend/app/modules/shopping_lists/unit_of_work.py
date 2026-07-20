from __future__ import annotations

from sqlmodel import Session

from app.modules.shopping_lists.ports import (
    ShoppingListRepositoryPort,
    ShoppingListUnitOfWorkPort,
    ShoppingShareRepositoryPort,
)
from app.modules.shopping_lists.repository import (
    SqlShoppingListRepository,
    SqlShoppingShareRepository,
)


class SqlShoppingListUnitOfWork(ShoppingListUnitOfWorkPort):
    def __init__(self, session: Session) -> None:
        self._session = session
        self._shopping_lists = SqlShoppingListRepository(session)
        self._shares = SqlShoppingShareRepository(session)

    @property
    def shopping_lists(self) -> ShoppingListRepositoryPort:
        return self._shopping_lists

    @property
    def shares(self) -> ShoppingShareRepositoryPort:
        return self._shares

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()

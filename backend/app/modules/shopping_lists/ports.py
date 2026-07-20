from __future__ import annotations

from abc import ABC, abstractmethod


class ShoppingListRepositoryPort(ABC):
    @abstractmethod
    def ensure_items(self, plan_id: int, items: list[dict]) -> list[dict]: ...

    @abstractmethod
    def list_items(self, plan_id: int) -> list[dict]: ...

    @abstractmethod
    def set_purchased(
        self, plan_id: int, item_id: int, purchased: bool
    ) -> dict | None: ...


class ShoppingShareRepositoryPort(ABC):
    @abstractmethod
    def get_or_create(self, plan_id: int) -> dict: ...

    @abstractmethod
    def get_active(self, share_id: str) -> dict | None: ...

    @abstractmethod
    def revoke(self, plan_id: int) -> None: ...


class ShoppingListUnitOfWorkPort(ABC):
    @property
    @abstractmethod
    def shopping_lists(self) -> ShoppingListRepositoryPort: ...

    @property
    @abstractmethod
    def shares(self) -> ShoppingShareRepositoryPort: ...

    @abstractmethod
    def commit(self) -> None: ...

    @abstractmethod
    def rollback(self) -> None: ...

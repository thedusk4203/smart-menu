# Repository interface (port). Infrastructure (repository.py) implements
# this; use_cases.py depends only on this abstraction, never on SQLModel.
from __future__ import annotations

from abc import ABC, abstractmethod

from app.modules.identity.domain import UserEntity


class UserRepositoryPort(ABC):
    @abstractmethod
    def list_all(self, limit: int, offset: int) -> list[UserEntity]: ...

    @abstractmethod
    def get_by_id(self, user_id: int) -> UserEntity | None: ...

    @abstractmethod
    def get_by_email(self, email: str) -> UserEntity | None: ...

    @abstractmethod
    def save(self, user: UserEntity) -> UserEntity: ...

    @abstractmethod
    def delete(self, user_id: int) -> None: ...

from __future__ import annotations

from abc import ABC, abstractmethod

from app.modules.profiles.domain import ExcludedIngredientEntity, UserProfileEntity


class UserProfileRepositoryPort(ABC):
    @abstractmethod
    def get_by_user(self, user_id: int) -> UserProfileEntity | None: ...

    @abstractmethod
    def create_empty(self, user_id: int, full_name: str | None) -> UserProfileEntity: ...

    @abstractmethod
    def save(self, profile: UserProfileEntity) -> UserProfileEntity: ...


class ExclusionRepositoryPort(ABC):
    @abstractmethod
    def list_by_user(self, user_id: int) -> list[ExcludedIngredientEntity]: ...

    @abstractmethod
    def get(self, user_id: int, ingredient_id: int) -> ExcludedIngredientEntity | None: ...

    @abstractmethod
    def add(self, item: ExcludedIngredientEntity) -> ExcludedIngredientEntity: ...

    @abstractmethod
    def remove(self, user_id: int, ingredient_id: int) -> None: ...

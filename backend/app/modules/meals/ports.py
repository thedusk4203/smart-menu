# File: backend/app/modules/meals/ports.py
from __future__ import annotations

from abc import ABC, abstractmethod

from app.modules.meals.domain import MealEntity, MealFullEntity, MealIngredientEntity


class MealRepositoryPort(ABC):
    @abstractmethod
    def list_summary(self, meal_type: str | None, search: str | None,
                      active_only: bool, limit: int, offset: int) -> list[MealFullEntity]: ...

    @abstractmethod
    def get_detail(self, meal_id: int) -> MealFullEntity | None: ...

    @abstractmethod
    def get(self, meal_id: int) -> MealEntity | None: ...

    @abstractmethod
    def create(self, meal: MealEntity, ingredients: list[MealIngredientEntity]) -> MealEntity: ...

    @abstractmethod
    def save(self, meal: MealEntity) -> MealEntity: ...

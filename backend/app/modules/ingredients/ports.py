# File: backend/app/modules/ingredients/ports.py
from __future__ import annotations

from abc import ABC, abstractmethod

from app.modules.ingredients.domain import IngredientEntity, IngredientFullEntity, NutritionFactsEntity


class IngredientRepositoryPort(ABC):
    @abstractmethod
    def list_full(self, food_group: str | None, search: str | None,
                  active_only: bool, limit: int, offset: int) -> list[IngredientFullEntity]: ...

    @abstractmethod
    def get_full(self, ingredient_id: int) -> IngredientFullEntity | None: ...

    @abstractmethod
    def get_by_name(self, name: str) -> IngredientEntity | None: ...

    @abstractmethod
    def get(self, ingredient_id: int) -> IngredientEntity | None: ...

    @abstractmethod
    def create(self, ingredient: IngredientEntity, nutrition: NutritionFactsEntity) -> IngredientEntity: ...

    @abstractmethod
    def save(self, ingredient: IngredientEntity) -> IngredientEntity: ...

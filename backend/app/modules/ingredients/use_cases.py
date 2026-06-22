# File: backend/app/modules/ingredients/use_cases.py
from __future__ import annotations

from app.modules.ingredients.domain import IngredientEntity, IngredientFullEntity, NutritionFactsEntity
from app.modules.ingredients.exceptions import IngredientNameExistsError, IngredientNotFoundError
from app.modules.ingredients.ports import IngredientRepositoryPort


class ListIngredientsUseCase:
    def __init__(self, repo: IngredientRepositoryPort) -> None:
        self._repo = repo

    def execute(self, food_group, search, active_only, limit, offset) -> list[IngredientFullEntity]:
        return self._repo.list_full(food_group, search, active_only, limit, offset)


class GetIngredientUseCase:
    def __init__(self, repo: IngredientRepositoryPort) -> None:
        self._repo = repo

    def execute(self, ingredient_id: int) -> IngredientFullEntity:
        item = self._repo.get_full(ingredient_id)
        if item is None:
            raise IngredientNotFoundError(ingredient_id)
        return item


class CreateIngredientUseCase:
    def __init__(self, repo: IngredientRepositoryPort) -> None:
        self._repo = repo

    def execute(self, name: str, food_group, default_unit: str, grams_per_unit: float,
                nutrition: NutritionFactsEntity) -> IngredientFullEntity:
        if self._repo.get_by_name(name) is not None:
            raise IngredientNameExistsError(name)
        ingredient = IngredientEntity(id=None, name=name, food_group=food_group,
                                       default_unit=default_unit, grams_per_unit=grams_per_unit)
        created = self._repo.create(ingredient, nutrition)
        return self._repo.get_full(created.id)


class UpdateIngredientUseCase:
    def __init__(self, repo: IngredientRepositoryPort) -> None:
        self._repo = repo

    def execute(self, ingredient_id: int, **changes) -> IngredientFullEntity:
        item = self._repo.get(ingredient_id)
        if item is None:
            raise IngredientNotFoundError(ingredient_id)
        updated = IngredientEntity(**{**item.__dict__, **changes})
        self._repo.save(updated)
        return self._repo.get_full(ingredient_id)


class DeactivateIngredientUseCase:
    """Xoá mềm — đánh dấu is_active=False thay vì xoá cứng (tôn trọng FK)."""
    def __init__(self, repo: IngredientRepositoryPort) -> None:
        self._repo = repo

    def execute(self, ingredient_id: int) -> None:
        item = self._repo.get(ingredient_id)
        if item is None:
            raise IngredientNotFoundError(ingredient_id)
        updated = IngredientEntity(**{**item.__dict__, "is_active": False})
        self._repo.save(updated)

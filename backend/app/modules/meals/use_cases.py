# File: backend/app/modules/meals/use_cases.py
from __future__ import annotations

from app.modules.meals.domain import MealEntity, MealFullEntity, MealIngredientEntity
from app.modules.meals.exceptions import MealNotFoundError
from app.modules.meals.ports import MealRepositoryPort


class ListMealsUseCase:
    def __init__(self, repo: MealRepositoryPort) -> None:
        self._repo = repo

    def execute(self, meal_type, search, active_only, limit, offset) -> list[MealFullEntity]:
        return self._repo.list_summary(meal_type, search, active_only, limit, offset)


class GetMealUseCase:
    def __init__(self, repo: MealRepositoryPort) -> None:
        self._repo = repo

    def execute(self, meal_id: int) -> MealFullEntity:
        meal = self._repo.get_detail(meal_id)
        if meal is None:
            raise MealNotFoundError(meal_id)
        return meal


class CreateMealUseCase:
    def __init__(self, repo: MealRepositoryPort) -> None:
        self._repo = repo

    def execute(self, name, meal_type, cooking_method, description, instructions,
                servings, tags, ingredients: list[MealIngredientEntity]) -> MealFullEntity:
        meal = MealEntity(id=None, name=name, meal_type=meal_type, cooking_method=cooking_method,
                           description=description, instructions=instructions,
                           servings=servings, tags=tags)
        created = self._repo.create(meal, ingredients)
        return self._repo.get_detail(created.id)


class UpdateMealUseCase:
    def __init__(self, repo: MealRepositoryPort) -> None:
        self._repo = repo

    def execute(self, meal_id: int, **changes) -> MealFullEntity:
        meal = self._repo.get(meal_id)
        if meal is None:
            raise MealNotFoundError(meal_id)
        updated = MealEntity(**{**meal.__dict__, **changes})
        self._repo.save(updated)
        return self._repo.get_detail(meal_id)


class DeactivateMealUseCase:
    def __init__(self, repo: MealRepositoryPort) -> None:
        self._repo = repo

    def execute(self, meal_id: int) -> None:
        meal = self._repo.get(meal_id)
        if meal is None:
            raise MealNotFoundError(meal_id)
        updated = MealEntity(**{**meal.__dict__, "is_active": False})
        self._repo.save(updated)

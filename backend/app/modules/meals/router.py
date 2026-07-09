# File: backend/app/modules/meals/router.py
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status

from app.dependencies import (
    get_create_meal_use_case,
    get_deactivate_meal_use_case,
    get_get_meal_use_case,
    get_list_meals_use_case,
    get_update_meal_use_case,
)
from app.modules.meals.domain import MealIngredientEntity
from app.modules.meals.schemas import MealCreate, MealDetail, MealSummary, MealUpdate
from app.modules.meals.use_cases import (
    CreateMealUseCase,
    DeactivateMealUseCase,
    GetMealUseCase,
    ListMealsUseCase,
    UpdateMealUseCase,
)
from app.shared.enums import MealType

router = APIRouter(prefix="/api/meals", tags=["meals"])


@router.get("", response_model=list[MealSummary])
def list_meals(
    meal_type: MealType | None = None, search: str | None = None, active_only: bool = True,
    limit: int = Query(100, le=500), offset: int = 0,
    use_case: ListMealsUseCase = Depends(get_list_meals_use_case),
):
    return use_case.execute(meal_type.value if meal_type else None, search, active_only, limit, offset)


@router.get("/{meal_id}", response_model=MealDetail)
def get_meal(meal_id: int, use_case: GetMealUseCase = Depends(get_get_meal_use_case)):
    return use_case.execute(meal_id)


@router.post("", response_model=MealDetail, status_code=status.HTTP_201_CREATED)
def create_meal(data: MealCreate, use_case: CreateMealUseCase = Depends(get_create_meal_use_case)):
    ingredients = [MealIngredientEntity(ingredient_id=i.ingredient_id, quantity=i.quantity, unit=i.unit)
                   for i in data.ingredients]
    return use_case.execute(data.name, data.meal_type, data.cooking_method, data.description,
                             data.instructions, data.servings, data.tags, data.components, ingredients)


@router.put("/{meal_id}", response_model=MealDetail)
def update_meal(meal_id: int, data: MealUpdate, use_case: UpdateMealUseCase = Depends(get_update_meal_use_case)):
    return use_case.execute(meal_id, **data.model_dump(exclude_unset=True))


@router.delete("/{meal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meal(meal_id: int, use_case: DeactivateMealUseCase = Depends(get_deactivate_meal_use_case)):
    use_case.execute(meal_id)

# File: backend/app/modules/ingredients/router.py
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status

from app.dependencies import (
    get_create_ingredient_use_case,
    get_deactivate_ingredient_use_case,
    get_get_ingredient_use_case,
    get_list_ingredients_use_case,
    get_update_ingredient_use_case,
)
from app.modules.ingredients.domain import NutritionFactsEntity
from app.modules.ingredients.schemas import IngredientCreate, IngredientResponse, IngredientUpdate
from app.modules.ingredients.use_cases import (
    CreateIngredientUseCase,
    DeactivateIngredientUseCase,
    GetIngredientUseCase,
    ListIngredientsUseCase,
    UpdateIngredientUseCase,
)
from app.shared.enums import FoodGroup

router = APIRouter(prefix="/api/ingredients", tags=["ingredients"])


@router.get("", response_model=list[IngredientResponse])
def list_ingredients(
    food_group: FoodGroup | None = None, search: str | None = None, active_only: bool = True,
    limit: int = Query(100, le=500), offset: int = 0,
    use_case: ListIngredientsUseCase = Depends(get_list_ingredients_use_case),
):
    return use_case.execute(
        food_group.value if food_group else None, search, active_only, limit, offset
    )


@router.get("/{ingredient_id}", response_model=IngredientResponse)
def get_ingredient(ingredient_id: int, use_case: GetIngredientUseCase = Depends(get_get_ingredient_use_case)):
    return use_case.execute(ingredient_id)


@router.post("", response_model=IngredientResponse, status_code=status.HTTP_201_CREATED)
def create_ingredient(
    data: IngredientCreate,
    use_case: CreateIngredientUseCase = Depends(get_create_ingredient_use_case),
):
    nutrition = NutritionFactsEntity(ingredient_id=0, **data.nutrition.model_dump())
    return use_case.execute(data.name, data.food_group, data.default_unit, data.grams_per_unit, nutrition)


@router.put("/{ingredient_id}", response_model=IngredientResponse)
def update_ingredient(
    ingredient_id: int, data: IngredientUpdate,
    use_case: UpdateIngredientUseCase = Depends(get_update_ingredient_use_case),
):
    return use_case.execute(ingredient_id, **data.model_dump(exclude_unset=True))


@router.delete("/{ingredient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ingredient(
    ingredient_id: int, use_case: DeactivateIngredientUseCase = Depends(get_deactivate_ingredient_use_case),
):
    use_case.execute(ingredient_id)

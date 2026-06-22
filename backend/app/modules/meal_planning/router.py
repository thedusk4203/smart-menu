# File: backend/app/modules/meal_planning/router.py
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status

from app.dependencies import (
    get_delete_meal_plan_use_case,
    get_get_meal_plan_use_case,
    get_list_meal_plans_use_case,
    get_save_meal_plan_use_case,
)
from app.modules.meal_planning.domain import MealPlanEntity
from app.modules.meal_planning.schemas import MealPlanCreate, MealPlanResponse
from app.modules.meal_planning.use_cases import (
    DeleteMealPlanUseCase,
    GetMealPlanUseCase,
    ListMealPlansUseCase,
    SaveMealPlanUseCase,
)

router = APIRouter(prefix="/api/meal-plans", tags=["meal-plans"])


@router.post("", response_model=MealPlanResponse, status_code=status.HTTP_201_CREATED)
def save_plan(data: MealPlanCreate, use_case: SaveMealPlanUseCase = Depends(get_save_meal_plan_use_case)):
    plan = MealPlanEntity(id=None, **data.model_dump())
    return use_case.execute(plan).__dict__


@router.get("", response_model=list[MealPlanResponse])
def list_plans(
    user_id: int = Query(...), use_case: ListMealPlansUseCase = Depends(get_list_meal_plans_use_case)
):
    return [p.__dict__ for p in use_case.execute(user_id)]


@router.get("/{plan_id}", response_model=MealPlanResponse)
def get_plan(plan_id: int, use_case: GetMealPlanUseCase = Depends(get_get_meal_plan_use_case)):
    return use_case.execute(plan_id).__dict__


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plan(plan_id: int, use_case: DeleteMealPlanUseCase = Depends(get_delete_meal_plan_use_case)):
    use_case.execute(plan_id)

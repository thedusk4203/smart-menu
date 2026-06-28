# File: backend/app/modules/meal_planning/router.py
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status

from app.dependencies import (
    get_build_plan_request_use_case,
    get_delete_meal_plan_use_case,
    get_generate_meal_plan_use_case,
    get_get_meal_plan_use_case,
    get_list_meal_plans_use_case,
    get_save_meal_plan_use_case,
)
from app.modules.meal_planning.domain import MealPlanEntity, ValidationResult
from app.modules.meal_planning.schemas import (
    GeneratedMealPlanResponse,
    GenerateMealPlanRequest,
    InfeasiblePlanResponse,
    MealPlanCreate,
    MealPlanResponse,
)
from app.modules.meal_planning.use_cases import (
    BuildPlanRequestUseCase,
    DeleteMealPlanUseCase,
    GenerateMealPlanUseCase,
    GetMealPlanUseCase,
    ListMealPlansUseCase,
    SaveMealPlanUseCase,
)

router = APIRouter(prefix="/api/meal-plans", tags=["meal-plans"])


@router.post("", response_model=MealPlanResponse, status_code=status.HTTP_201_CREATED)
def save_plan(data: MealPlanCreate, use_case: SaveMealPlanUseCase = Depends(get_save_meal_plan_use_case)):
    plan = MealPlanEntity(id=None, **data.model_dump())
    return use_case.execute(plan).__dict__


@router.post(
    "/generate",
    response_model=GeneratedMealPlanResponse | InfeasiblePlanResponse,
)
def generate_plan(
    data: GenerateMealPlanRequest,
    build_request: BuildPlanRequestUseCase = Depends(get_build_plan_request_use_case),
    generate: GenerateMealPlanUseCase = Depends(get_generate_meal_plan_use_case),
):
    """Sinh thực đơn tự động (không tự lưu). Trả thực đơn vừa sinh, hoặc
    {status: "infeasible", reasons: [...]} nếu không thể lập."""
    request = build_request.execute(
        data.user_id,
        days=data.days,
        meals_per_day=data.meals_per_day,
        budget_limit=data.budget_limit,
        preferred_tags=data.preferred_tags,
    )
    result = generate.execute(request)

    if isinstance(result, ValidationResult):
        # Gộp lý do bất khả thi + vi phạm cứng để client hiển thị.
        reasons = list(result.infeasible_reasons) + list(result.hard_violations)
        return InfeasiblePlanResponse(status="infeasible", reasons=reasons)

    return GeneratedMealPlanResponse(
        user_id=result.user_id,
        name=result.name,
        start_date=result.start_date,
        end_date=result.end_date,
        budget_limit=result.budget_limit,
        total_cost=result.total_cost,
        total_calories=result.total_calories,
        plan_data=result.plan_data,
    )


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

# File: backend/app/modules/meal_planning/router.py
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_current_user
from app.dependencies import (
    get_build_plan_request_use_case,
    get_delete_meal_plan_use_case,
    get_generate_meal_plan_use_case,
    get_get_meal_plan_use_case,
    get_list_meal_plans_use_case,
    get_save_meal_plan_use_case,
)
from app.modules.identity.domain import UserEntity
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


def _ensure_owner(plan: MealPlanEntity, current_user: UserEntity) -> None:
    """Chỉ chủ sở hữu hoặc admin được thao tác trên thực đơn (chống IDOR)."""
    if plan.user_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Không có quyền với thực đơn này")


@router.post("", response_model=MealPlanResponse, status_code=status.HTTP_201_CREATED)
def save_plan(
    data: MealPlanCreate,
    current_user: UserEntity = Depends(get_current_user),
    use_case: SaveMealPlanUseCase = Depends(get_save_meal_plan_use_case),
):
    """Lưu thực đơn: backend reload mâm cơm theo id và tự tính totals/plan_data;
    KHÔNG tin total_cost/total_calories/plan_data client gửi. Gắn user từ JWT."""
    return use_case.execute(data, user_id=current_user.id).__dict__


@router.post(
    "/generate",
    response_model=GeneratedMealPlanResponse | InfeasiblePlanResponse,
)
def generate_plan(
    data: GenerateMealPlanRequest,
    current_user: UserEntity = Depends(get_current_user),
    build_request: BuildPlanRequestUseCase = Depends(get_build_plan_request_use_case),
    generate: GenerateMealPlanUseCase = Depends(get_generate_meal_plan_use_case),
):
    """Sinh thực đơn tự động (không tự lưu) cho người dùng hiện tại (JWT).
    Trả thực đơn vừa sinh, hoặc {status: "infeasible", reasons: [...]}."""
    request = build_request.execute(
        current_user.id,
        days=data.days,
        meals_per_day=data.meals_per_day,
        budget_limit=data.budget_limit,
        preferred_tags=data.preferred_tags,
    )
    result = generate.execute(request, seed=data.seed)

    if isinstance(result, ValidationResult):
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
    current_user: UserEntity = Depends(get_current_user),
    use_case: ListMealPlansUseCase = Depends(get_list_meal_plans_use_case),
):
    return [p.__dict__ for p in use_case.execute(current_user.id)]


@router.get("/{plan_id}", response_model=MealPlanResponse)
def get_plan(
    plan_id: int,
    current_user: UserEntity = Depends(get_current_user),
    use_case: GetMealPlanUseCase = Depends(get_get_meal_plan_use_case),
):
    plan = use_case.execute(plan_id)  # 404 nếu không tồn tại
    _ensure_owner(plan, current_user)
    return plan.__dict__


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plan(
    plan_id: int,
    current_user: UserEntity = Depends(get_current_user),
    get_use_case: GetMealPlanUseCase = Depends(get_get_meal_plan_use_case),
    delete_use_case: DeleteMealPlanUseCase = Depends(get_delete_meal_plan_use_case),
):
    plan = get_use_case.execute(plan_id)  # 404 nếu không tồn tại
    _ensure_owner(plan, current_user)
    delete_use_case.execute(plan_id)

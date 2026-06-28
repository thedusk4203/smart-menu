# File: backend/app/modules/meal_planning/schemas.py
from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class MealPlanCreate(BaseModel):
    user_id: int
    name: str = "Thực đơn tuần"
    start_date: date
    end_date: date | None = None
    budget_limit: float | None = None
    total_cost: float = 0
    total_calories: float = 0
    plan_data: dict = {}


class MealPlanResponse(BaseModel):
    id: int
    user_id: int
    name: str
    start_date: date
    end_date: date | None
    budget_limit: float | None
    total_cost: float
    total_calories: float
    plan_data: dict

    class Config:
        from_attributes = True


class GenerateMealPlanRequest(BaseModel):
    """Body cho POST /api/meal-plans/generate. days/meals_per_day/budget_limit
    có thể bỏ trống — khi đó lấy mặc định từ hồ sơ người dùng (xem
    BuildPlanRequestUseCase)."""
    user_id: int
    days: int | None = None
    meals_per_day: int | None = None
    budget_limit: float | None = None
    preferred_tags: list[str] | None = None


class GeneratedMealPlanResponse(BaseModel):
    """Thực đơn vừa sinh (CHƯA lưu — id=None). Client gọi POST /api/meal-plans
    để lưu nếu muốn giữ lại."""
    user_id: int
    name: str
    start_date: date | None
    end_date: date | None
    budget_limit: float | None
    total_cost: float
    total_calories: float
    plan_data: dict


class InfeasiblePlanResponse(BaseModel):
    """Trả về khi không thể lập thực đơn hợp lệ (vi phạm ràng buộc cứng)."""
    status: str = "infeasible"
    reasons: list[str] = []

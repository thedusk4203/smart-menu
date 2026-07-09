from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class SavedMealSlot(BaseModel):
    """Một lựa chọn của client cho một slot: chỉ tên slot + id mâm cơm.
    Backend KHÔNG tin dinh dưỡng/giá client gửi — reload theo id để recompute."""
    slot: str
    meal_set_id: int


class SavedPlanDay(BaseModel):
    day: int
    meals: list[SavedMealSlot]


class MealPlanCreate(BaseModel):
    """Hợp đồng lưu thực đơn (Gate 0): client chỉ gửi tên + ngày bắt đầu +
    các id mâm cơm theo ngày/slot. Backend tự tính totals/plan_data từ nguồn
    đúng; không nhận user_id/total_cost/total_calories/plan_data từ client."""
    name: str = "Thực đơn tuần"
    start_date: date
    budget_limit: float | None = None
    days: list[SavedPlanDay]


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
    days: int | None = None
    meals_per_day: int | None = None
    budget_limit: float | None = None
    preferred_tags: list[str] | None = None
    # seed cho "tạo lại thực đơn khác" (FR-PLAN-05): None = chọn tối ưu deterministic;
    # có giá trị = xáo trộn có kiểm soát để ra phương án khác. Client gửi số ngẫu nhiên.
    seed: int | None = None


class GeneratedMealPlanResponse(BaseModel):
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

# File: backend/app/modules/meal_planning/exceptions.py
from __future__ import annotations

from app.core.exceptions import NotFoundError


class MealPlanNotFoundError(NotFoundError):
    def __init__(self, plan_id: int) -> None:
        super().__init__(f"Không tìm thấy thực đơn id={plan_id}")

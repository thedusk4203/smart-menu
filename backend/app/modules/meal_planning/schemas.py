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

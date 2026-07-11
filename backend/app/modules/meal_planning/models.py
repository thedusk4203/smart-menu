# File: backend/app/modules/meal_planning/models.py
from __future__ import annotations

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from datetime import date, datetime

from sqlmodel import Field, SQLModel


class MealPlanModel(SQLModel, table=True):
    __tablename__ = "meal_plans"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int
    name: str = "Thực đơn"
    start_date: date  # date — SQLModel suy ra kiểu DATE qua annotation thật bên dưới
    end_date: date | None = None
    budget_limit: float | None = None
    total_cost: float = 0
    total_calories: float = 0
    plan_data: dict = Field(default_factory=dict, sa_column=Column(JSONB, nullable=False))
    created_at: datetime | None = None

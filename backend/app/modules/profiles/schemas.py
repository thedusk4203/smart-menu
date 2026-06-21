# File: backend/app/modules/profiles/schemas.py
from __future__ import annotations

from pydantic import BaseModel

from app.shared.enums import ActivityLevel, ExclusionReason, FitnessGoal, Gender


class ProfileResponse(BaseModel):
    user_id: int
    full_name: str | None
    gender: Gender | None
    age: int | None
    height_cm: float | None
    weight_kg: float | None
    activity_level: ActivityLevel
    goal: FitnessGoal
    meals_per_day: int
    daily_calorie_target: float | None
    daily_budget: float | None

    class Config:
        from_attributes = True


class ProfileUpdate(BaseModel):
    full_name: str | None = None
    gender: Gender | None = None
    age: int | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    activity_level: ActivityLevel | None = None
    goal: FitnessGoal | None = None
    meals_per_day: int | None = None
    daily_calorie_target: float | None = None
    daily_budget: float | None = None


class ExclusionCreate(BaseModel):
    ingredient_id: int
    reason: ExclusionReason = ExclusionReason.DISLIKE


class ExclusionResponse(BaseModel):
    id: int
    ingredient_id: int
    reason: ExclusionReason

    class Config:
        from_attributes = True

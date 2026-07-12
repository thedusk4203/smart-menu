# SQLModel ORM models — map to user_profiles và user_excluded_ingredients
# (tạo bởi data/init_db.sql).
from __future__ import annotations

from sqlalchemy import Column
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel

from app.shared.enums import ActivityLevel, ExclusionReason, FitnessGoal, Gender


class UserProfileModel(SQLModel, table=True):
    __tablename__ = "user_profiles"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int
    full_name: str | None = None
    gender: Gender | None = Field(
        default=None, sa_column=Column(SAEnum(Gender, name="gender", values_callable=lambda obj: [e.value for e in obj], create_type=False), nullable=True)
    )
    age: int | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    activity_level: ActivityLevel = Field(
        sa_column=Column(SAEnum(ActivityLevel, name="activity_level", values_callable=lambda obj: [e.value for e in obj], create_type=False), nullable=False)
    )
    goal: FitnessGoal = Field(
        sa_column=Column(SAEnum(FitnessGoal, name="physical_goal", values_callable=lambda obj: [e.value for e in obj], create_type=False), nullable=False)
    )
    meals_per_day: int = 3
    daily_calorie_target: float | None = None
    daily_budget: float | None = None


class UserExcludedIngredientModel(SQLModel, table=True):
    __tablename__ = "user_excluded_ingredients"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int
    ingredient_id: int
    reason: ExclusionReason = Field(
        sa_column=Column(SAEnum(ExclusionReason, name="exclusion_reason", values_callable=lambda obj: [e.value for e in obj], create_type=False), nullable=False)
    )

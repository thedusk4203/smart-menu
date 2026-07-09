# File: backend/app/modules/meals/models.py
from __future__ import annotations

from sqlalchemy import Column
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

from app.shared.enums import CookingMethod, MealType


class MealModel(SQLModel, table=True):
    __tablename__ = "meals"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    meal_type: MealType = Field(
        sa_column=Column(SAEnum(MealType, name="meal_type", values_callable=lambda obj: [e.value for e in obj], create_type=False), nullable=False)
    )
    cooking_method: CookingMethod | None = Field(
        default=None,
        sa_column=Column(SAEnum(CookingMethod, name="cooking_method", values_callable=lambda obj: [e.value for e in obj], create_type=False), nullable=True),
    )
    description: str | None = None
    instructions: str | None = None
    servings: int = 1
    tags: list = Field(default_factory=list, sa_column=Column(JSONB, nullable=False))
    components: list = Field(default_factory=list, sa_column=Column(JSONB, nullable=False))
    is_active: bool = True


class MealIngredientModel(SQLModel, table=True):
    __tablename__ = "meal_ingredients"

    id: int | None = Field(default=None, primary_key=True)
    meal_id: int
    ingredient_id: int
    quantity: float
    unit: str = "g"

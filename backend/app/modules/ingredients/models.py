# File: backend/app/modules/ingredients/models.py
# SQLModel ORM models — map to ingredients, nutrition_facts (tạo bởi
# data/init_db.sql). v_ingredients_full được đọc trực tiếp bằng raw SQL
# trong repository.py (không có model ORM cho view).
from __future__ import annotations

from sqlalchemy import Column
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel

from app.shared.enums import FoodGroup


class IngredientModel(SQLModel, table=True):
    __tablename__ = "ingredients"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    food_group: FoodGroup = Field(
        sa_column=Column(SAEnum(FoodGroup, name="food_group", values_callable=lambda obj: [e.value for e in obj], create_type=False), nullable=False)
    )
    default_unit: str = "g"
    grams_per_unit: float = 1
    is_active: bool = True


class NutritionFactsModel(SQLModel, table=True):
    __tablename__ = "nutrition_facts"

    id: int | None = Field(default=None, primary_key=True)
    ingredient_id: int
    calories: float = 0
    protein_g: float = 0
    carbs_g: float = 0
    fat_g: float = 0
    fiber_g: float = 0

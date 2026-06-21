# File: backend/app/modules/ingredients/schemas.py
from __future__ import annotations

from pydantic import BaseModel

from app.shared.enums import FoodGroup


class IngredientResponse(BaseModel):
    id: int
    name: str
    food_group: FoodGroup
    default_unit: str
    grams_per_unit: float
    is_active: bool
    calories: float | None = None
    protein_g: float | None = None
    carbs_g: float | None = None
    fat_g: float | None = None
    fiber_g: float | None = None
    latest_price: float | None = None
    price_unit: str | None = None
    latest_price_per_unit: float | None = None


class NutritionInput(BaseModel):
    calories: float = 0
    protein_g: float = 0
    carbs_g: float = 0
    fat_g: float = 0
    fiber_g: float = 0


class IngredientCreate(BaseModel):
    name: str
    food_group: FoodGroup
    default_unit: str = "g"
    grams_per_unit: float = 1
    nutrition: NutritionInput = NutritionInput()


class IngredientUpdate(BaseModel):
    name: str | None = None
    food_group: FoodGroup | None = None
    default_unit: str | None = None
    grams_per_unit: float | None = None
    is_active: bool | None = None

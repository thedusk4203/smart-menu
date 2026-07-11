# File: backend/app/modules/meals/schemas.py
from __future__ import annotations

from pydantic import BaseModel

from app.shared.enums import CookingMethod, MealType


class MealIngredientInput(BaseModel):
    ingredient_id: int
    quantity: float
    unit: str = "g"


class MealIngredientResponse(BaseModel):
    ingredient_id: int
    name: str | None = None
    quantity: float
    unit: str


class MealSummary(BaseModel):
    id: int
    name: str
    meal_type: MealType
    cooking_method: CookingMethod | None = None
    servings: int
    tags: list = []
    components: list[str] = []
    is_active: bool
    total_calories: float
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float
    estimated_cost: float


class MealDetail(MealSummary):
    description: str | None = None
    instructions: str | None = None
    ingredients: list[MealIngredientResponse] = []


class MealCreate(BaseModel):
    name: str
    meal_type: MealType
    cooking_method: CookingMethod | None = None
    description: str | None = None
    instructions: str | None = None
    servings: int = 1
    tags: list = []
    components: list[str] = []
    ingredients: list[MealIngredientInput] = []


class MealUpdate(BaseModel):
    name: str | None = None
    meal_type: MealType | None = None
    cooking_method: CookingMethod | None = None
    description: str | None = None
    instructions: str | None = None
    servings: int | None = None
    tags: list | None = None
    components: list[str] | None = None
    is_active: bool | None = None

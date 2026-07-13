from __future__ import annotations

from pydantic import BaseModel, Field

from app.shared.enums import CookingMethod, DishType


class DishIngredientResponse(BaseModel):
    ingredient_id: int
    name: str
    quantity: float
    unit: str
    estimated_cost: float = 0


class DishSummaryResponse(BaseModel):
    id: int
    name: str
    dish_type: DishType
    cooking_method: CookingMethod | None = None
    tags: list[str] = Field(default_factory=list)
    total_calories: float
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float
    estimated_cost: float


class DishDetailResponse(DishSummaryResponse):
    description: str | None = None
    instructions: str | None = None
    ingredients: list[DishIngredientResponse] = Field(default_factory=list)

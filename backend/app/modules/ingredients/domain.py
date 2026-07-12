from __future__ import annotations

from dataclasses import dataclass

from app.shared.enums import FoodGroup


@dataclass(frozen=True)
class IngredientEntity:
    id: int | None
    name: str
    food_group: FoodGroup
    default_unit: str = "g"
    grams_per_unit: float = 1.0  # quy đổi mọi nguyên liệu về gram (trứng/quả, dầu/ml...)
    is_active: bool = True


@dataclass(frozen=True)
class NutritionFactsEntity:
    """Dinh dưỡng trên 100g nguyên liệu."""
    ingredient_id: int
    calories: float = 0
    protein_g: float = 0
    carbs_g: float = 0
    fat_g: float = 0
    fiber_g: float = 0


@dataclass(frozen=True)
class IngredientFullEntity:
    """Nguyên liệu kèm dinh dưỡng + giá mới nhất — đọc qua view v_ingredients_full."""
    id: int
    name: str
    food_group: str
    default_unit: str
    grams_per_unit: float
    is_active: bool
    calories: float | None
    protein_g: float | None
    carbs_g: float | None
    fat_g: float | None
    fiber_g: float | None
    latest_price: float | None
    price_unit: str | None
    latest_price_per_unit: float | None

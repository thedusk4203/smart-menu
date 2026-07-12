from __future__ import annotations

from dataclasses import dataclass, field

from app.shared.enums import CookingMethod, MealType


@dataclass(frozen=True)
class MealIngredientEntity:
    ingredient_id: int
    quantity: float
    unit: str = "g"
    name: str | None = None  # điền khi đọc (join với ingredients), bỏ trống khi tạo


@dataclass(frozen=True)
class MealEntity:
    id: int | None
    name: str
    meal_type: MealType
    cooking_method: CookingMethod | None = None
    description: str | None = None
    instructions: str | None = None
    servings: int = 1
    tags: list = field(default_factory=list)
    components: list[str] = field(default_factory=list)
    is_active: bool = True


@dataclass(frozen=True)
class MealFullEntity:
    """Bữa/món kèm tổng dinh dưỡng + chi phí ước tính — đọc qua view v_meals_full."""
    id: int
    name: str
    meal_type: str
    cooking_method: str | None
    servings: int
    tags: list
    components: list[str]
    is_active: bool
    total_calories: float
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float
    estimated_cost: float
    description: str | None = None
    instructions: str | None = None
    ingredients: list = field(default_factory=list)

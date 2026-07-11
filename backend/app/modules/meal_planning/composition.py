"""Quy tắc ghép meal cố định, độc lập với solver và API."""
from __future__ import annotations

from collections import Counter

from app.modules.meal_planning.domain import ComposedMeal, DishCandidate
from app.shared.enums import DishType, MealType


BREAKFAST_RULE = {DishType.BREAKFAST: 1}
MAIN_MEAL_RULE = {
    DishType.STAPLE: 1,
    DishType.SAVORY: 1,
    "side_choice": (DishType.VEGETABLE_SIDE, DishType.SOUP),
}


def slots_for(meals_per_day: int) -> tuple[MealType, ...]:
    if meals_per_day == 2:
        return (MealType.LUNCH, MealType.DINNER)
    if meals_per_day == 3:
        return (MealType.BREAKFAST, MealType.LUNCH, MealType.DINNER)
    raise ValueError("meals_per_day phải là 2 hoặc 3")


def is_main_slot(slot: MealType | str) -> bool:
    return str(slot) in {MealType.LUNCH.value, MealType.DINNER.value}


def valid_meal_types(meal: ComposedMeal) -> bool:
    types = Counter(d.dish_type for d in meal.dishes)
    if meal.slot == MealType.BREAKFAST:
        return len(meal.dishes) == 1 and types == BREAKFAST_RULE
    if meal.slot in (MealType.LUNCH, MealType.DINNER):
        return (
            len(meal.dishes) == 3
            and types[DishType.STAPLE] == 1
            and types[DishType.SAVORY] == 1
            and types[DishType.VEGETABLE_SIDE] + types[DishType.SOUP] == 1
            and sum(types.values()) == 3
        )
    return False


def canonical_dishes_for_meal(meal: ComposedMeal) -> tuple[DishCandidate, ...]:
    """Ổn định thứ tự hiển thị/snapshot: tinh bột, mặn, rau/canh."""
    order = {
        DishType.BREAKFAST: 0,
        DishType.STAPLE: 0,
        DishType.SAVORY: 1,
        DishType.VEGETABLE_SIDE: 2,
        DishType.SOUP: 2,
    }
    return tuple(sorted(meal.dishes, key=lambda dish: (order[dish.dish_type], dish.dish_id)))

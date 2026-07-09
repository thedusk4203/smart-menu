# File: backend/app/tests/test_meal_planning/factories.py
# Factory dùng chung cho test thuật toán sinh thực đơn — dựng MealCandidate /
# PlanRequest bằng dữ liệu giả, KHÔNG cần DB (planner/scorer/constraint_checker
# đều là hàm thuần).
from __future__ import annotations

from app.modules.meal_planning.domain import MealCandidate, PlanRequest


def make_candidate(
    meal_id: int,
    *,
    name: str | None = None,
    meal_type: str = "breakfast",
    calories: float = 400.0,
    protein: float = 20.0,
    fat: float = 10.0,
    carb: float = 50.0,
    cost: float = 20000.0,
    ingredient_ids: list[int] | None = None,
    tags: list[str] | None = None,
    components: list[str] | None = None,
    dishes: list[dict] | None = None,
) -> MealCandidate:
    return MealCandidate(
        meal_id=meal_id,
        name=name or f"Món {meal_id}",
        meal_type=meal_type,
        total_calories=calories,
        total_protein_g=protein,
        total_fat_g=fat,
        total_carb_g=carb,
        estimated_cost=cost,
        ingredient_ids=list(ingredient_ids or []),
        tags=list(tags or []),
        components=list(components or []),
        dishes=list(dishes or []),
    )


def make_request(
    *,
    user_id: int = 1,
    days: int = 1,
    meals_per_day: int = 2,
    budget_limit: float | None = 200000.0,
    target_calories: float = 2000.0,
    target_protein_g: float = 120.0,
    target_fat_g: float = 60.0,
    target_carb_g: float = 250.0,
    excluded: list[int] | None = None,
    preferred_tags: list[str] | None = None,
) -> PlanRequest:
    return PlanRequest(
        user_id=user_id,
        days=days,
        meals_per_day=meals_per_day,
        budget_limit=budget_limit,
        target_calories=target_calories,
        target_protein_g=target_protein_g,
        target_fat_g=target_fat_g,
        target_carb_g=target_carb_g,
        excluded_ingredient_ids=list(excluded or []),
        preferred_tags=list(preferred_tags or []),
    )

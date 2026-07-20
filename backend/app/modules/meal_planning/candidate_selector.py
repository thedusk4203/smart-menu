"""Catalog bounding and regenerate constraints shared by Planner V3 phases."""
from __future__ import annotations

import math

from ortools.sat.python import cp_model

from app.modules.meal_planning.domain import DishCandidate, PlanRequest, QualityPolicy
from app.modules.meal_planning.quality import DEFAULT_QUALITY_POLICY
from app.shared.enums import DishType, MealType


class CandidateSelector:
    def __init__(self, policy: QualityPolicy = DEFAULT_QUALITY_POLICY) -> None:
        self._policy = policy

    def shortlist(self, request: PlanRequest, candidates: list[DishCandidate]) -> list[DishCandidate]:
        preferred = {tag.casefold() for tag in request.preferred_tags}
        main_uses = request.days * 2
        groups = (
            ({DishType.BREAKFAST}, request.days),
            ({DishType.STAPLE}, main_uses),
            ({DishType.SAVORY}, main_uses),
            ({DishType.VEGETABLE_SIDE, DishType.SOUP}, main_uses),
        )
        shortlisted: list[DishCandidate] = []
        for dish_types, required_uses in groups:
            pool = [item for item in candidates if item.dish_type in dish_types]
            uses_per_candidate = 1 if request.days <= 3 else 2
            capacity = math.ceil(required_uses / uses_per_candidate) + 3
            cap = min(len(pool), min(12, max(8, capacity)))
            if len(pool) <= cap:
                shortlisted.extend(pool)
                continue
            nutrition_ranked = sorted(
                pool, key=lambda item: (self._meal_nutrition_score(request, item), item.dish_id)
            )
            cheapest = sorted(pool, key=lambda item: (item.estimated_cost, item.dish_id))
            tagged = [
                item for item in nutrition_ranked
                if preferred.intersection(tag.casefold() for tag in item.tags)
            ]
            best_by_method: list[DishCandidate] = []
            seen_methods = set()
            for item in nutrition_ranked:
                if item.cooking_method is not None and item.cooking_method not in seen_methods:
                    seen_methods.add(item.cooking_method)
                    best_by_method.append(item)
            nutrition_axis = sorted(
                pool,
                key=lambda item: (
                    item.calories, item.protein_g, item.fat_g, item.carb_g, item.dish_id
                ),
            )
            spread_count = min(len(nutrition_axis), max(2, cap // 2))
            spread = [
                nutrition_axis[round(index * (len(nutrition_axis) - 1) / max(1, spread_count - 1))]
                for index in range(spread_count)
            ]
            chosen: dict[int, DishCandidate] = {}

            def add(sequence: list[DishCandidate], limit: int) -> None:
                added = 0
                for item in sequence:
                    if item.dish_id in chosen:
                        continue
                    chosen[item.dish_id] = item
                    added += 1
                    if len(chosen) >= cap or added >= limit:
                        break

            add(cheapest, min(required_uses, cap) if request.budget_limit is not None else 2)
            add(tagged, max(2, cap // 4))
            add(best_by_method, cap)
            add(spread, spread_count)
            add(nutrition_ranked, cap)
            shortlisted.extend(chosen.values())
        return sorted(shortlisted, key=lambda item: item.dish_id)

    def _meal_nutrition_score(self, request: PlanRequest, dish: DishCandidate) -> float:
        divisor = float(request.meals_per_day)
        return (
            abs(dish.calories - request.target_calories / divisor)
            * self._policy.calorie_deviation_weight
            + max(0, request.target_protein_g / divisor - dish.protein_g)
            * self._policy.protein_shortage_weight
            + abs(dish.fat_g - request.target_fat_g / divisor)
            * self._policy.macro_deviation_weight
            + abs(dish.carb_g - request.target_carb_g / divisor)
            * self._policy.macro_deviation_weight
        )


def add_regenerate_difference(
    model: cp_model.CpModel,
    variables: dict[tuple[int, MealType, int], cp_model.IntVar],
    signature: str | None,
) -> None:
    if not signature:
        return
    previous: list[cp_model.IntVar] = []
    for item in signature.split("|"):
        try:
            day, slot, dish_id = item.split(":")
            key = (int(day) - 1, MealType(slot), int(dish_id))
        except (TypeError, ValueError):
            continue
        if key in variables:
            previous.append(variables[key])
    if previous:
        model.Add(sum(previous) <= len(previous) - 1)

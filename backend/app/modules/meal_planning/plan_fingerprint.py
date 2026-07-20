from __future__ import annotations

import hashlib
import json

from app.modules.meal_planning.domain import ComposedMeal, PlanRequest


def source_fingerprint(request: PlanRequest, days: list[list[ComposedMeal]]) -> str:
    payload = {
        "request": {
            "days": request.days,
            "meals_per_day": request.meals_per_day,
            "budget_limit": request.budget_limit,
            "targets": [
                request.target_calories,
                request.target_protein_g,
                request.target_fat_g,
                request.target_carb_g,
            ],
            "inventory_fingerprint": request.inventory_fingerprint,
        },
        "inventory_lots": [lot.__dict__ for lot in request.inventory_lots],
        "dishes": [
            {
                "id": dish.dish_id,
                "nutrition": [dish.calories, dish.protein_g, dish.fat_g, dish.carb_g],
                "ingredients": [ingredient.__dict__ for ingredient in dish.ingredients],
            }
            for day in days
            for meal in day
            for dish in meal.dishes
        ],
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()

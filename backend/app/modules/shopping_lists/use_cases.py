from __future__ import annotations

from collections import defaultdict
from typing import Protocol

from app.modules.meal_planning.domain import MealPlanEntity
from app.modules.shopping_lists.schemas import ShoppingListResponse


class LegacyDishRecipeProvider(Protocol):
    def load_ingredients(self, dish_ids: list[int]) -> list[dict]: ...


class BuildShoppingListUseCase:
    def __init__(self, legacy_recipe_provider: LegacyDishRecipeProvider, list_repo=None) -> None:
        self._legacy_recipe_provider = legacy_recipe_provider
        self._list_repo = list_repo

    def execute(self, plan: MealPlanEntity) -> ShoppingListResponse:
        schema_version = int(plan.plan_data.get("schema_version", 1))
        if schema_version >= 2:
            items = self._from_v2_snapshot(plan.plan_data)
            warnings: list[dict] = []
        else:
            items, warnings = self._from_v1_best_effort(plan.plan_data)
        if self._list_repo is not None and plan.id:
            items = self._list_repo.ensure_items(plan.id, items)
        return ShoppingListResponse(
            plan_id=plan.id or 0,
            plan_name=plan.name,
            schema_version=schema_version,
            items=items,
            total_estimated_cost=round(sum(item["estimated_cost"] for item in items), 0),
            warnings=warnings,
        )

    @staticmethod
    def _aggregate(rows: list[dict]) -> list[dict]:
        grouped: dict[tuple[int, str], dict] = {}
        for row in rows:
            ingredient_id = int(row["ingredient_id"])
            unit = str(row["unit"])
            key = (ingredient_id, unit)
            target = grouped.setdefault(
                key,
                {
                    "ingredient_id": ingredient_id,
                    "name": str(row["name"]),
                    "quantity": 0.0,
                    "unit": unit,
                    "estimated_cost": 0.0,
                },
            )
            target["quantity"] += float(row.get("quantity", 0))
            target["estimated_cost"] += float(row.get("estimated_cost", 0))
        return [
            {**item, "quantity": round(item["quantity"], 2), "estimated_cost": round(item["estimated_cost"], 0)}
            for item in sorted(grouped.values(), key=lambda item: (item["name"].casefold(), item["unit"]))
        ]

    def _from_v2_snapshot(self, plan_data: dict) -> list[dict]:
        ingredients: list[dict] = []
        for day in plan_data.get("days", []):
            for meal in day.get("meals", []):
                for dish in meal.get("dishes", []):
                    ingredients.extend(dish.get("ingredients", []))
        return self._aggregate(ingredients)

    def _from_v1_best_effort(self, plan_data: dict) -> tuple[list[dict], list[dict]]:
        dish_ids = sorted(
            {
                int(dish["dish_id"])
                for day in plan_data.get("days", [])
                for meal in day.get("meals", [])
                for dish in meal.get("dishes", [])
                if isinstance(dish, dict) and dish.get("dish_id")
            }
        )
        if not dish_ids:
            return [], [{"code": "LEGACY_PLAN_NO_DISH_SNAPSHOT", "message": "Plan V1 không có dish snapshot để tạo shopping list."}]
        # Need preserve repeat count in V1: reload once per dish ID then multiply based
        # on its occurrences in plan data.
        occurrences: defaultdict[int, int] = defaultdict(int)
        for day in plan_data.get("days", []):
            for meal in day.get("meals", []):
                for dish in meal.get("dishes", []):
                    if isinstance(dish, dict) and dish.get("dish_id"):
                        occurrences[int(dish["dish_id"])] += 1
        rows = []
        for row in self._legacy_recipe_provider.load_ingredients(dish_ids):
            copied = dict(row)
            multiplier = occurrences[int(copied["dish_id"])]
            copied["quantity"] = float(copied["quantity"]) * multiplier
            copied["estimated_cost"] = float(copied["estimated_cost"]) * multiplier
            rows.append(copied)
        return self._aggregate(rows), [
            {"code": "LEGACY_PLAN_USES_CURRENT_RECIPE", "message": "Plan V1 dùng công thức và giá hiện tại theo best effort."}
        ]

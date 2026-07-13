from __future__ import annotations

from collections import defaultdict
from typing import Protocol

from app.modules.meal_planning.domain import MealPlanEntity
from app.modules.shopping_lists.exceptions import ShoppingListDayNotFoundError
from app.modules.shopping_lists.schemas import ShoppingListResponse


class LegacyDishRecipeProvider(Protocol):
    def load_ingredients(self, dish_ids: list[int]) -> list[dict]: ...


class BuildShoppingListUseCase:
    def __init__(self, legacy_recipe_provider: LegacyDishRecipeProvider, list_repo=None) -> None:
        self._legacy_recipe_provider = legacy_recipe_provider
        self._list_repo = list_repo

    def execute(self, plan: MealPlanEntity, day: int | None = None) -> ShoppingListResponse:
        selected_day = self._selected_day(plan.plan_data, day)
        schema_version = int(plan.plan_data.get("schema_version", 1))
        if schema_version >= 2:
            all_items = self._from_v2_snapshot(plan.plan_data)
            items = all_items if day is None else self._from_v2_snapshot(plan.plan_data, day)
            warnings: list[dict] = []
        else:
            recipe_rows, warnings = self._load_v1_recipes(plan.plan_data)
            all_items = self._from_v1_rows(plan.plan_data, recipe_rows)
            items = all_items if day is None else self._from_v1_rows(plan.plan_data, recipe_rows, day)
        if self._list_repo is not None and plan.id:
            persisted_items = self._list_repo.ensure_items(plan.id, all_items)
            items = persisted_items if day is None else self._with_persisted_state(items, persisted_items)
        return ShoppingListResponse(
            plan_id=plan.id or 0,
            plan_name=plan.name,
            day=day,
            date=selected_day.get("date") if selected_day else None,
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

    @staticmethod
    def _selected_day(plan_data: dict, day: int | None) -> dict | None:
        if day is None:
            return None
        for index, plan_day in enumerate(plan_data.get("days", []), start=1):
            if int(plan_day.get("day", index)) == day:
                return plan_day
        raise ShoppingListDayNotFoundError(day)

    @classmethod
    def _days_in_scope(cls, plan_data: dict, day: int | None) -> list[dict]:
        if day is None:
            return list(plan_data.get("days", []))
        return [cls._selected_day(plan_data, day)]

    def _from_v2_snapshot(self, plan_data: dict, day: int | None = None) -> list[dict]:
        ingredients: list[dict] = []
        for plan_day in self._days_in_scope(plan_data, day):
            for meal in plan_day.get("meals", []):
                for dish in meal.get("dishes", []):
                    ingredients.extend(dish.get("ingredients", []))
        return self._aggregate(ingredients)

    def _load_v1_recipes(self, plan_data: dict) -> tuple[list[dict], list[dict]]:
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
        return self._legacy_recipe_provider.load_ingredients(dish_ids), [
            {"code": "LEGACY_PLAN_USES_CURRENT_RECIPE", "message": "Plan V1 dùng công thức và giá hiện tại theo best effort."}
        ]

    def _from_v1_rows(self, plan_data: dict, recipe_rows: list[dict], day: int | None = None) -> list[dict]:
        occurrences: defaultdict[int, int] = defaultdict(int)
        for plan_day in self._days_in_scope(plan_data, day):
            for meal in plan_day.get("meals", []):
                for dish in meal.get("dishes", []):
                    if isinstance(dish, dict) and dish.get("dish_id"):
                        occurrences[int(dish["dish_id"])] += 1
        rows = []
        for row in recipe_rows:
            copied = dict(row)
            multiplier = occurrences.get(int(copied["dish_id"]), 0)
            if multiplier == 0:
                continue
            copied["quantity"] = float(copied["quantity"]) * multiplier
            copied["estimated_cost"] = float(copied["estimated_cost"]) * multiplier
            rows.append(copied)
        return self._aggregate(rows)

    @staticmethod
    def _with_persisted_state(items: list[dict], persisted_items: list[dict]) -> list[dict]:
        persisted_by_key = {
            (int(item["ingredient_id"]), str(item["unit"])): item
            for item in persisted_items
        }
        result: list[dict] = []
        for item in items:
            persisted = persisted_by_key.get((int(item["ingredient_id"]), str(item["unit"])), {})
            result.append({
                **item,
                "id": persisted.get("id"),
                "is_purchased": bool(persisted.get("is_purchased", False)),
            })
        return result

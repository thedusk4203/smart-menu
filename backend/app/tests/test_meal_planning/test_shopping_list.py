from __future__ import annotations

from app.modules.meal_planning.domain import MealPlanEntity
from app.modules.shopping_lists.use_cases import BuildShoppingListUseCase


class FakeLegacyRecipes:
    def load_ingredients(self, dish_ids: list[int]) -> list[dict]:
        return [
            {"dish_id": dish_id, "ingredient_id": 1, "name": "Gạo", "quantity": 100, "unit": "g", "estimated_cost": 2_000}
            for dish_id in dish_ids
        ]


def test_v2_shopping_list_uses_saved_snapshot_not_live_recipe():
    plan = MealPlanEntity(
        id=7,
        user_id=1,
        plan_data={
            "schema_version": 2,
            "days": [{"meals": [{"dishes": [{"ingredients": [
                {"ingredient_id": 1, "name": "Gạo", "quantity": 200, "unit": "g", "estimated_cost": 4_000},
                {"ingredient_id": 1, "name": "Gạo", "quantity": 100, "unit": "g", "estimated_cost": 2_000},
            ]}]}]}],
        },
    )
    result = BuildShoppingListUseCase(FakeLegacyRecipes()).execute(plan)
    assert result.schema_version == 2
    assert result.items[0].quantity == 300
    assert result.items[0].estimated_cost == 6_000
    assert result.warnings == []


def test_v1_shopping_list_warns_and_reloads_current_dish_recipe():
    plan = MealPlanEntity(
        id=8,
        user_id=1,
        plan_data={
            "days": [{"meals": [{"dishes": [{"dish_id": 10}, {"dish_id": 10}]}]}],
        },
    )
    result = BuildShoppingListUseCase(FakeLegacyRecipes()).execute(plan)
    assert result.items[0].quantity == 200
    assert result.warnings[0].code == "LEGACY_PLAN_USES_CURRENT_RECIPE"

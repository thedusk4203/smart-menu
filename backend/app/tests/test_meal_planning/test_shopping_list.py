from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.modules.meal_planning.domain import MealPlanEntity
from app.modules.identity.domain import UserEntity
from app.modules.shopping_lists.exceptions import ShoppingListDayNotFoundError
from app.modules.shopping_lists.router import (
    _read_share_token,
    _share_token,
    share_shopping_list,
)
from app.modules.shopping_lists.use_cases import BuildShoppingListUseCase


class FakeLegacyRecipes:
    def load_ingredients(self, dish_ids: list[int]) -> list[dict]:
        return [
            {"dish_id": dish_id, "ingredient_id": 1, "name": "Gạo", "quantity": 100, "unit": "g", "estimated_cost": 2_000}
            for dish_id in dish_ids
        ]


class FakeShoppingListRepository:
    def __init__(self) -> None:
        self.materialized_items: list[dict] = []

    def ensure_items(self, plan_id: int, items: list[dict]) -> list[dict]:
        self.materialized_items = items
        return [
            {**item, "id": index, "is_purchased": item["ingredient_id"] == 1}
            for index, item in enumerate(items, start=1)
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


def test_shopping_list_can_select_one_day_and_keeps_purchased_state():
    plan = MealPlanEntity(
        id=9,
        user_id=1,
        plan_data={
            "schema_version": 2,
            "days": [
                {"day": 1, "date": "2026-07-13", "meals": [{"dishes": [{"ingredients": [
                    {"ingredient_id": 1, "name": "Gạo", "quantity": 200, "unit": "g", "estimated_cost": 4_000},
                ]}]}]},
                {"day": 2, "date": "2026-07-14", "meals": [{"dishes": [{"ingredients": [
                    {"ingredient_id": 1, "name": "Gạo", "quantity": 100, "unit": "g", "estimated_cost": 2_000},
                    {"ingredient_id": 2, "name": "Trứng", "quantity": 2, "unit": "quả", "estimated_cost": 6_000},
                ]}]}]},
            ],
        },
    )
    repository = FakeShoppingListRepository()

    result = BuildShoppingListUseCase(FakeLegacyRecipes(), repository).execute(plan, day=2)

    assert result.day == 2
    assert result.date.isoformat() == "2026-07-14"
    assert result.total_estimated_cost == 8_000
    assert [(item.name, item.quantity) for item in result.items] == [("Gạo", 100), ("Trứng", 2)]
    assert result.items[0].id == 1
    assert result.items[0].is_purchased is True
    assert repository.materialized_items[0]["quantity"] == 300


def test_shopping_list_rejects_day_outside_selected_plan():
    plan = MealPlanEntity(
        id=10,
        user_id=1,
        plan_data={"schema_version": 2, "days": [{"day": 1, "meals": []}]},
    )

    with pytest.raises(ShoppingListDayNotFoundError):
        BuildShoppingListUseCase(FakeLegacyRecipes()).execute(plan, day=2)


def test_shared_shopping_list_token_preserves_selected_day():
    share = {
        "id": "00000000-0000-0000-0000-000000000001",
        "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
    }

    share_id, day = _read_share_token(_share_token(share, day=3))

    assert share_id == share["id"]
    assert day == 3


def test_share_response_confirms_selected_day():
    plan = MealPlanEntity(
        id=11,
        user_id=1,
        plan_data={"schema_version": 2, "days": [{"day": 2, "meals": []}]},
    )
    share = {
        "id": "00000000-0000-0000-0000-000000000002",
        "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
    }

    class FakePlans:
        def execute(self, plan_id: int):
            assert plan_id == plan.id
            return plan

    class FakeBuild:
        def execute(self, selected_plan, day: int | None = None):
            assert selected_plan is plan
            assert day == 2

    class FakeShares:
        def get_or_create(self, plan_id: int):
            assert plan_id == plan.id
            return share

    response = share_shopping_list(
        plan_id=plan.id,
        day=2,
        current_user=UserEntity(id=1, email="owner@example.com", hashed_password="hash"),
        plans=FakePlans(),
        build=FakeBuild(),
        shares=FakeShares(),
    )

    assert response.day == 2
    assert _read_share_token(response.token)[1] == 2

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone

import pytest

from app.modules.meal_planning.domain import MealPlanEntity
from app.modules.identity.domain import UserEntity
from app.modules.shopping_lists.exceptions import ShoppingListScopeError
from app.modules.shopping_lists.router import (
    _read_share_token,
    _share_token,
    share_shopping_list,
)
from app.modules.shopping_lists.use_cases import (
    BuildShoppingListUseCase,
    UpdateShoppingItemsUseCase,
)


class FakeShoppingListRepository:
    def __init__(self) -> None:
        self.materialized_items: list[dict] = []

    def ensure_items(self, plan_id: int, items: list[dict]) -> list[dict]:
        self.materialized_items = items
        return [
            {**item, "id": index, "is_purchased": item["ingredient_id"] == 1}
            for index, item in enumerate(items, start=1)
        ]

    def set_purchased_many(
        self, plan_id: int, item_ids: list[int], purchased: bool
    ) -> int:
        self.updated_many = (plan_id, item_ids, purchased)
        return len(item_ids)


class FakeShoppingUnitOfWork:
    def __init__(self, repository: FakeShoppingListRepository) -> None:
        self.shopping_lists = repository
        self.commits = 0
        self.rollbacks = 0

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


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
        plan_data={"schema_version": 3, "days": [{"day": 2, "meals": []}]},
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
        def execute(self, selected_plan, day: int | None = None, scope: str | None = None):
            assert selected_plan is plan
            assert day == 2
            assert scope == "usage_day"

    class FakeShares:
        def execute(self, plan_id: int):
            assert plan_id == plan.id
            return share

    response = share_shopping_list(
        plan_id=plan.id,
        day=2,
        current_user=UserEntity(id=1, email="owner@example.com", hashed_password="hash"),
        plans=FakePlans(),
        build=FakeBuild(),
        create_share=FakeShares(),
    )

    assert response.day == 2
    assert _read_share_token(response.token)[1] == 2


def _v3_plan() -> MealPlanEntity:
    return MealPlanEntity(
        id=12,
        user_id=1,
        name="Plan V3",
        plan_data={
            "schema_version": 3,
            "cost_summary": {
                "purchase_cost": 5_000,
                "consumption_value": 3_800,
                "expired_waste_value": 0,
                "ending_carryover_value": 1_200,
            },
            "procurement": {
                "ledger_version": 2,
                "shopping_days": [1, 2],
                "purchase_items": [
                    {
                        "item_key": "purchase:1:1",
                        "ingredient_id": 1,
                        "name": "Thịt gà",
                        "unit": "g",
                        "purchase_day": 1,
                        "purchase_increment": 100,
                        "block_count": 2,
                        "required_quantity": 180,
                        "purchase_quantity": 200,
                        "purchase_cost": 4_000,
                        "price_per_default_unit": 20,
                        "remaining_quantity": 20,
                        "expired_waste_quantity": 0,
                        "carryover_quantity": 20,
                        "storage_splits": [{"mode": "fridge", "quantity": 200, "expiry_day": 3}],
                        "allocations": [
                            {
                                "day": 1, "quantity": 100, "storage_mode": "room",
                                "expiry_day": 1, "dish_name": "Gà áp chảo",
                            },
                            {
                                "day": 2, "quantity": 80, "storage_mode": "fridge",
                                "expiry_day": 3, "dish_name": "Gà xào",
                            },
                        ],
                    },
                    {
                        "item_key": "purchase:2:2",
                        "ingredient_id": 2,
                        "name": "Rau cải",
                        "unit": "g",
                        "purchase_day": 2,
                        "purchase_increment": 100,
                        "block_count": 1,
                        "required_quantity": 100,
                        "purchase_quantity": 100,
                        "purchase_cost": 1_000,
                        "price_per_default_unit": 10,
                        "remaining_quantity": 0,
                        "expired_waste_quantity": 0,
                        "carryover_quantity": 0,
                        "storage_splits": [{"mode": "room", "quantity": 100, "expiry_day": 2}],
                        "allocations": [
                            {
                                "day": 2, "quantity": 100, "storage_mode": "room",
                                "expiry_day": 2, "dish_name": "Rau luộc",
                            }
                        ],
                    },
                ],
                "pantry_checks": [
                    {
                        "item_key": "pantry:3",
                        "ingredient_id": 3,
                        "name": "Hạt tiêu",
                        "quantity": 2,
                        "unit": "g",
                    }
                ],
                "daily_ledger": [
                    {
                        "day": 1,
                        "items": [{
                            "item_key": "purchase:1:1", "source_kind": "purchase",
                            "inventory_lot_id": None, "ingredient_id": 1,
                            "name": "Thịt gà", "unit": "g", "opening_quantity": 0,
                            "purchase_quantity": 200, "usage_quantity": 100,
                            "expired_quantity": 0, "closing_quantity": 100,
                            "unit_value": 20, "purchase_cost": 4_000,
                            "allocations": [{
                                "day": 1, "quantity": 100, "storage_mode": "room",
                                "expiry_day": 1, "dish_name": "Gà áp chảo",
                            }],
                        }],
                        "totals": {},
                    },
                    {
                        "day": 2,
                        "items": [
                            {
                                "item_key": "purchase:1:1", "source_kind": "purchase",
                                "inventory_lot_id": None, "ingredient_id": 1,
                                "name": "Thịt gà", "unit": "g", "opening_quantity": 100,
                                "purchase_quantity": 0, "usage_quantity": 80,
                                "expired_quantity": 0, "closing_quantity": 20,
                                "unit_value": 20, "purchase_cost": 0,
                                "allocations": [{
                                    "day": 2, "quantity": 80, "storage_mode": "fridge",
                                    "expiry_day": 3, "dish_name": "Gà xào",
                                }],
                            },
                            {
                                "item_key": "purchase:2:2", "source_kind": "purchase",
                                "inventory_lot_id": None, "ingredient_id": 2,
                                "name": "Rau cải", "unit": "g", "opening_quantity": 0,
                                "purchase_quantity": 100, "usage_quantity": 100,
                                "expired_quantity": 0, "closing_quantity": 0,
                                "unit_value": 10, "purchase_cost": 1_000,
                                "allocations": [{
                                    "day": 2, "quantity": 100, "storage_mode": "room",
                                    "expiry_day": 2, "dish_name": "Rau luộc",
                                }],
                            },
                        ],
                        "totals": {},
                    },
                ],
            },
            "days": [
                {
                    "day": 1,
                    "date": "2026-07-19",
                    "meals": [{"dishes": [{"ingredients": []}]}],
                },
                {
                    "day": 2,
                    "date": "2026-07-20",
                    "meals": [{"dishes": [{"ingredients": [
                        {"ingredient_id": 3, "purchase_mode": "pantry"}
                    ]}]}],
                },
            ],
        },
    )


def test_v3_shopping_list_exposes_purchase_blocks_pantry_and_cost_hierarchy():
    repository = FakeShoppingListRepository()
    unit_of_work = FakeShoppingUnitOfWork(repository)

    result = BuildShoppingListUseCase(unit_of_work).execute(_v3_plan())

    assert result.shopping_schema_version == 3
    assert result.scope == "all"
    assert [(item.item_key, item.purchase_quantity) for item in result.purchase_items] == [
        ("purchase:1:1", 200),
        ("purchase:2:2", 100),
    ]
    assert result.purchase_items[0].is_purchased is True
    assert result.pantry_checks[0].name == "Hạt tiêu"
    assert result.total_estimated_cost == 5_000
    assert result.summary["purchase_cost"] == 5_000
    assert result.summary["visible_purchase_cost"] == 5_000
    assert len(repository.materialized_items) == 3
    assert unit_of_work.commits == 1


def test_bulk_purchase_update_deduplicates_ids_and_commits_once():
    repository = FakeShoppingListRepository()
    unit_of_work = FakeShoppingUnitOfWork(repository)

    updated = UpdateShoppingItemsUseCase(unit_of_work).execute(
        plan_id=12, item_ids=[1, 2, 1], purchased=True
    )

    assert updated is True
    assert repository.updated_many == (12, [1, 2], True)
    assert unit_of_work.commits == 1
    assert unit_of_work.rollbacks == 0


def test_bulk_purchase_update_rolls_back_when_any_item_is_missing():
    repository = FakeShoppingListRepository()
    repository.set_purchased_many = lambda plan_id, item_ids, purchased: 1
    unit_of_work = FakeShoppingUnitOfWork(repository)

    updated = UpdateShoppingItemsUseCase(unit_of_work).execute(
        plan_id=12, item_ids=[1, 2], purchased=True
    )

    assert updated is False
    assert unit_of_work.commits == 0
    assert unit_of_work.rollbacks == 1


def test_v3_usage_day_distinguishes_new_purchase_from_fridge_carryover():
    result = BuildShoppingListUseCase().execute(
        _v3_plan(), day=2, scope="usage_day"
    )

    assert result.date.isoformat() == "2026-07-20"
    assert [item.ingredient_id for item in result.purchase_items] == [2]
    assert {item.ingredient_id for item in result.pantry_checks} == {3}
    assert [(item.ingredient_id, item.purchase_day, item.storage_mode) for item in result.carryover_usage] == [
        (1, 1, "fridge"),
    ]
    assert result.leftovers[0].status == "closing_stock"


def test_v3_purchase_day_scope_requires_a_day_and_filters_visible_cost():
    use_case = BuildShoppingListUseCase()

    with pytest.raises(ShoppingListScopeError):
        use_case.execute(_v3_plan(), scope="purchase_day")

    result = use_case.execute(_v3_plan(), day=1, scope="purchase_day")
    assert [item.ingredient_id for item in result.purchase_items] == [1]
    assert result.summary["visible_purchase_cost"] == 4_000


def test_v3_ledger_usage_day_reports_true_day_end_stock():
    plan = deepcopy(_v3_plan())
    plan.plan_data["procurement"]["inventory_items"] = []
    plan.plan_data["procurement"]["daily_ledger"] = [
        {
            "day": 1,
            "items": [{
                "item_key": "purchase:1:1", "source_kind": "purchase",
                "inventory_lot_id": None, "ingredient_id": 1, "name": "Thịt gà", "unit": "g",
                "opening_quantity": 0, "purchase_quantity": 200, "usage_quantity": 100,
                "expired_quantity": 0, "closing_quantity": 100, "unit_value": 20,
                "purchase_cost": 4_000, "allocations": [],
            }],
            "totals": {"opening_value": 0, "purchase_cost": 4_000, "usage_value": 2_000, "expired_value": 0, "closing_value": 2_000},
        },
        {
            "day": 2,
            "items": [{
                "item_key": "purchase:1:1", "source_kind": "purchase",
                "inventory_lot_id": None, "ingredient_id": 1, "name": "Thịt gà", "unit": "g",
                "opening_quantity": 100, "purchase_quantity": 0, "usage_quantity": 80,
                "expired_quantity": 0, "closing_quantity": 20, "unit_value": 20,
                "purchase_cost": 0, "allocations": [],
            }],
            "totals": {"opening_value": 2_000, "purchase_cost": 0, "usage_value": 1_600, "expired_value": 0, "closing_value": 400},
        },
    ]

    result = BuildShoppingListUseCase().execute(plan, day=1, scope="usage_day")

    assert result.shopping_schema_version == 3
    assert result.daily_ledger[0].items[0].closing_quantity == 100
    assert result.leftovers[0].quantity == 100
    assert result.leftovers[0].status == "closing_stock"

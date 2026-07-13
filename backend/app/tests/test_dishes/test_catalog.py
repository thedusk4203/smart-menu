from __future__ import annotations

from app.modules.dishes.router import get_dish, list_dishes
from app.shared.enums import DishType


def test_catalog_lists_planner_ready_dishes(db_session):
    items = list_dishes(
        search=None,
        dish_type=None,
        limit=100,
        offset=0,
        session=db_session,
    )

    assert items
    assert all(item["total_calories"] > 0 for item in items)
    assert all(item["estimated_cost"] > 0 for item in items)


def test_catalog_filters_by_type_and_returns_detail(db_session):
    breakfasts = list_dishes(
        search=None,
        dish_type=DishType.BREAKFAST,
        limit=10,
        offset=0,
        session=db_session,
    )

    assert breakfasts
    assert all(item["dish_type"] == DishType.BREAKFAST.value for item in breakfasts)

    detail = get_dish(breakfasts[0]["id"], session=db_session)
    assert detail["id"] == breakfasts[0]["id"]
    assert detail["ingredients"]
    assert all(item["quantity"] > 0 for item in detail["ingredients"])

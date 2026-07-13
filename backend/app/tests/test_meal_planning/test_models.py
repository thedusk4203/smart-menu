from __future__ import annotations

from app.modules.meal_planning.models import MealPlanModel


def test_meal_plan_model_populates_created_at_before_insert():
    row = MealPlanModel(user_id=1, start_date="2026-07-13")

    assert row.created_at is not None

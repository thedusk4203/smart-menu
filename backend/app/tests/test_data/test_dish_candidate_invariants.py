from __future__ import annotations

from sqlalchemy import text

from app.modules.meal_planning.dish_candidate_repository import SqlDishCandidateProvider
from app.shared.enums import DishType


def test_seed_has_planner_ready_pool_for_every_required_role(db_session):
    rows = db_session.execute(
        text("SELECT dish_type, COUNT(*) FROM v_dish_candidates GROUP BY dish_type")
    ).fetchall()
    counts = {str(row.dish_type): row.count for row in rows}
    assert counts[DishType.BREAKFAST.value] >= 1
    assert counts[DishType.STAPLE.value] >= 1
    assert counts[DishType.SAVORY.value] >= 1
    assert counts[DishType.VEGETABLE_SIDE.value] + counts[DishType.SOUP.value] >= 1


def test_candidate_view_only_returns_complete_dishes(db_session):
    invalid = db_session.execute(
        text(
            """SELECT id FROM v_dish_candidates
               WHERE ingredient_count = 0
                  OR NOT all_ingredients_active
                  OR NOT has_complete_nutrition
                  OR NOT has_complete_price
                  OR total_calories <= 0
                  OR estimated_cost <= 0"""
        )
    ).fetchall()
    assert invalid == []


def test_dish_provider_exclusion_and_batch_mapping(db_session):
    provider = SqlDishCandidateProvider(db_session)
    all_candidates = provider.load_candidates([])
    assert all_candidates == sorted(all_candidates, key=lambda candidate: candidate.dish_id)
    excluded = all_candidates[0].ingredient_ids[0]
    filtered = provider.load_candidates([excluded])
    assert all(excluded not in candidate.ingredient_ids for candidate in filtered)
    selected_ids = [candidate.dish_id for candidate in all_candidates[:3]]
    by_id = provider.load_by_ids(selected_ids)
    assert list(by_id) == selected_ids
    assert all(candidate.ingredients for candidate in by_id.values())


def test_inactive_ingredient_removes_related_dish_from_candidate_view(db_session):
    row = db_session.execute(
        text("SELECT dish_id, ingredient_id FROM dish_ingredients ORDER BY dish_id, ingredient_id LIMIT 1")
    ).first()
    savepoint = db_session.begin_nested()
    try:
        db_session.execute(text("UPDATE ingredients SET is_active = FALSE WHERE id = :id"), {"id": row.ingredient_id})
        still_visible = db_session.execute(
            text("SELECT 1 FROM v_dish_candidates WHERE id = :dish_id"), {"dish_id": row.dish_id}
        ).first()
        assert still_visible is None
    finally:
        savepoint.rollback()

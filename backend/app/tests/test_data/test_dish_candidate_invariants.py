from __future__ import annotations

from sqlalchemy import text
import pytest

from app.modules.meal_planning.dish_candidate_repository import SqlDishCandidateProvider
from app.shared.enums import DishType


@pytest.fixture
def planner_catalog(db_session):
    """Dữ liệu tối thiểu, tự tạo cho từng test thay vì phụ thuộc DB seed."""
    savepoint = db_session.begin_nested()
    try:
        ingredient_ids: list[int] = []
        for index, dish_type in enumerate((
            DishType.BREAKFAST,
            DishType.STAPLE,
            DishType.SAVORY,
            DishType.VEGETABLE_SIDE,
        ), start=1):
            ingredient_id = db_session.execute(
                text("""INSERT INTO ingredients (name, food_group, default_unit, grams_per_unit, is_active)
                        VALUES (:name, 'protein', 'g', 1, TRUE) RETURNING id"""),
                {"name": f"Test planner ingredient {dish_type.value}"},
            ).scalar_one()
            ingredient_ids.append(ingredient_id)
            db_session.execute(
                text("""INSERT INTO nutrition_facts
                        (ingredient_id, calories, protein_g, carbs_g, fat_g, fiber_g)
                        VALUES (:id, 100, 10, 10, 5, 1)"""),
                {"id": ingredient_id},
            )
            db_session.execute(
                text("""INSERT INTO price_snapshots
                        (ingredient_id, price, unit, price_per_default_unit, source)
                        VALUES (:id, 10000, 'g', 100, 'test')"""),
                {"id": ingredient_id},
            )
            dish_id = db_session.execute(
                text("""INSERT INTO dishes (name, dish_type, tags, is_active)
                        VALUES (:name, CAST(:dish_type AS dish_type), '[]'::jsonb, TRUE) RETURNING id"""),
                {"name": f"Test planner dish {dish_type.value}", "dish_type": dish_type.value},
            ).scalar_one()
            db_session.execute(
                text("""INSERT INTO dish_ingredients (dish_id, ingredient_id, quantity, unit)
                        VALUES (:dish_id, :ingredient_id, 100, 'g')"""),
                {"dish_id": dish_id, "ingredient_id": ingredient_id},
            )
        yield
    finally:
        savepoint.rollback()


def test_fixture_has_planner_ready_pool_for_every_required_role(db_session, planner_catalog):
    rows = db_session.execute(
        text("SELECT dish_type, COUNT(*) FROM v_dish_candidates GROUP BY dish_type")
    ).fetchall()
    counts = {str(row.dish_type): row.count for row in rows}
    assert counts[DishType.BREAKFAST.value] >= 1
    assert counts[DishType.STAPLE.value] >= 1
    assert counts[DishType.SAVORY.value] >= 1
    assert counts[DishType.VEGETABLE_SIDE.value] + counts[DishType.SOUP.value] >= 1


def test_candidate_view_only_returns_complete_dishes(db_session, planner_catalog):
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


def test_dish_provider_exclusion_and_batch_mapping(db_session, planner_catalog):
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


def test_inactive_ingredient_removes_related_dish_from_candidate_view(db_session, planner_catalog):
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

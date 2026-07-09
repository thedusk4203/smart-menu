# File: backend/app/tests/test_data/test_seed_invariants.py
# Invariant dữ liệu seed cho model `meals` CŨ (data/init_db.sql).
#
# CHỈ kiểm meals / v_meals_full (raw SQL). Invariant cho model MỚI
# (dishes/meal_sets) + candidate provider nằm ở test_meal_set_invariants.py —
# vì provider giờ đọc v_meal_candidates, tránh comment nói v_meals_full một đằng
# còn provider đọc một nẻo.
#
# Test TÍCH HỢP chạy trên Postgres thật (view dùng jsonb/LATERAL). Giữ để bảo vệ
# hợp đồng dữ liệu meals cũ đến khi Phase B deprecate.
from __future__ import annotations

from sqlalchemy import text


def test_active_meals_ingredients_have_nutrition(db_session):
    """Mọi nguyên liệu dùng trong món active phải có nutrition_facts."""
    rows = db_session.execute(text("""
        SELECT DISTINCT i.name
        FROM meals m
        JOIN meal_ingredients mi ON mi.meal_id = m.id
        JOIN ingredients i ON i.id = mi.ingredient_id
        LEFT JOIN nutrition_facts nf ON nf.ingredient_id = i.id
        WHERE m.is_active = TRUE AND nf.ingredient_id IS NULL
    """)).fetchall()
    assert not rows, (
        f"Nguyên liệu (dùng trong món active) thiếu nutrition_facts: {[r[0] for r in rows]}"
    )


def test_active_meals_ingredients_have_price(db_session):
    """Mọi nguyên liệu dùng trong món active phải có giá mới nhất."""
    rows = db_session.execute(text("""
        SELECT DISTINCT i.name
        FROM meals m
        JOIN meal_ingredients mi ON mi.meal_id = m.id
        JOIN ingredients i ON i.id = mi.ingredient_id
        WHERE m.is_active = TRUE
          AND NOT EXISTS (
              SELECT 1 FROM price_snapshots ps
              WHERE ps.ingredient_id = i.id
                AND ps.price_per_default_unit IS NOT NULL
          )
    """)).fetchall()
    assert not rows, (
        f"Nguyên liệu (dùng trong món active) thiếu giá mới nhất: {[r[0] for r in rows]}"
    )


def test_every_active_meal_has_ingredients(db_session):
    """Không món active nào bị rỗng nguyên liệu (dấu hiệu JOIN theo tên trượt)."""
    rows = db_session.execute(text("""
        SELECT m.name FROM meals m
        WHERE m.is_active = TRUE
          AND NOT EXISTS (SELECT 1 FROM meal_ingredients mi WHERE mi.meal_id = m.id)
    """)).fetchall()
    assert not rows, f"Món active không có nguyên liệu nào: {[r[0] for r in rows]}"


def test_every_active_meal_has_positive_cost_and_calories(db_session):
    """HC-07 ở mức tổng hợp: cost > 0 và calo > 0."""
    rows = db_session.execute(text("""
        SELECT name FROM v_meals_full
        WHERE is_active = TRUE AND (total_calories <= 0 OR estimated_cost <= 0)
    """)).fetchall()
    assert not rows, f"Món active có calo hoặc chi phí <= 0: {[r[0] for r in rows]}"


def test_lunch_and_dinner_are_vietnamese_meal_sets(db_session):
    """Bữa trưa/tối trong seed cũ phải là một bữa cơm/combo, không phải món lẻ."""
    rows = db_session.execute(text("""
        SELECT name
        FROM meals
        WHERE is_active = TRUE
          AND meal_type IN ('lunch', 'dinner')
          AND jsonb_array_length(components) < 3
    """)).fetchall()
    assert not rows, (
        f"Bữa trưa/tối cần ít nhất 3 components (cơm + món mặn + rau/canh): "
        f"{[r[0] for r in rows]}"
    )

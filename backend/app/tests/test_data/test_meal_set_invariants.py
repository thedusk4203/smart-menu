# File: backend/app/tests/test_data/test_meal_set_invariants.py
# Invariant dữ liệu model MỚI (Phase A): dishes / meal_sets / v_meal_candidates.
#
# Test TÍCH HỢP chạy trên Postgres thật (view dùng jsonb/LATERAL/CTE). Bám sát
# hành vi planner: dùng chính SqlMealCandidateProvider + has_valid_data.
from __future__ import annotations

from sqlalchemy import text

from app.modules.meal_planning import constraint_checker
from app.modules.meal_planning.candidate_repository import SqlMealCandidateProvider

MEAL_TYPES = ("breakfast", "lunch", "dinner")
DEMO_USER_ID = 2
MIN_CANDIDATES_PER_SLOT = 3
# Vai trò bắt buộc trong mâm cơm trưa/tối kiểu Việt.
REQUIRED_LUNCH_DINNER_ROLES = ("savory", "soup", "vegetable_side")


def _valid_counts_by_type(candidates) -> dict[str, int]:
    counts = {t: 0 for t in MEAL_TYPES}
    for c in candidates:
        if c.meal_type in counts and constraint_checker.has_valid_data(c):
            counts[c.meal_type] += 1
    return counts


# --- Dish completeness (Layer A trên dishes/dish_ingredients) ---

def test_active_dish_ingredients_have_nutrition(db_session):
    rows = db_session.execute(text("""
        SELECT DISTINCT i.name
        FROM dishes d
        JOIN dish_ingredients di ON di.dish_id = d.id
        JOIN ingredients i ON i.id = di.ingredient_id
        LEFT JOIN nutrition_facts nf ON nf.ingredient_id = i.id
        WHERE d.is_active = TRUE AND nf.ingredient_id IS NULL
    """)).fetchall()
    assert not rows, f"Nguyên liệu (trong dish active) thiếu nutrition_facts: {[r[0] for r in rows]}"


def test_active_dish_ingredients_have_price(db_session):
    rows = db_session.execute(text("""
        SELECT DISTINCT i.name
        FROM dishes d
        JOIN dish_ingredients di ON di.dish_id = d.id
        JOIN ingredients i ON i.id = di.ingredient_id
        WHERE d.is_active = TRUE
          AND NOT EXISTS (
              SELECT 1 FROM price_snapshots ps
              WHERE ps.ingredient_id = i.id AND ps.price_per_default_unit IS NOT NULL
          )
    """)).fetchall()
    assert not rows, f"Nguyên liệu (trong dish active) thiếu giá: {[r[0] for r in rows]}"


def test_every_active_dish_has_ingredients_and_positive_values(db_session):
    rows = db_session.execute(text("""
        SELECT name FROM v_dishes_full
        WHERE is_active = TRUE
          AND (ingredient_count = 0 OR total_calories <= 0 OR estimated_cost <= 0)
    """)).fetchall()
    assert not rows, f"Dish active thiếu nguyên liệu/calo/chi phí: {[r[0] for r in rows]}"


# --- Meal_set composition + totals ---

def test_lunch_dinner_meal_sets_have_required_roles(db_session):
    sets = db_session.execute(text("""
        SELECT name, meal_type FROM meal_sets
        WHERE is_active = TRUE AND meal_type IN ('lunch', 'dinner')
    """)).fetchall()
    assert sets, "Chưa có meal_set lunch/dinner nào."
    for name, meal_type in sets:
        roles = {
            r[0] for r in db_session.execute(text("""
                SELECT DISTINCT msd.role
                FROM meal_set_dishes msd
                JOIN meal_sets ms ON ms.id = msd.meal_set_id
                WHERE ms.name = :n
            """), {"n": name}).fetchall()
        }
        for required in REQUIRED_LUNCH_DINNER_ROLES:
            assert required in roles, (
                f"Mâm {meal_type} '{name}' thiếu role '{required}' (có: {sorted(roles)})."
            )
        assert "staple" in roles, f"Mâm {meal_type} '{name}' nên có tinh bột (staple)."


def test_breakfast_meal_sets_have_at_least_one_dish(db_session):
    rows = db_session.execute(text("""
        SELECT ms.name FROM meal_sets ms
        WHERE ms.is_active = TRUE AND ms.meal_type = 'breakfast'
          AND NOT EXISTS (SELECT 1 FROM meal_set_dishes msd WHERE msd.meal_set_id = ms.id)
    """)).fetchall()
    assert not rows, f"Bữa sáng không có dish nào: {[r[0] for r in rows]}"


def test_meal_set_totals_equal_sum_of_dishes(db_session):
    rows = db_session.execute(text("""
        SELECT ms.name, mf.total_calories AS set_cal, mf.estimated_cost AS set_cost,
               COALESCE(s.cal, 0) AS dish_cal, COALESCE(s.cost, 0) AS dish_cost
        FROM meal_sets ms
        JOIN v_meal_sets_full mf ON mf.id = ms.id
        LEFT JOIN (
            SELECT msd.meal_set_id,
                   SUM(df.total_calories) AS cal,
                   SUM(df.estimated_cost) AS cost
            FROM meal_set_dishes msd
            JOIN v_dishes_full df ON df.id = msd.dish_id
            GROUP BY msd.meal_set_id
        ) s ON s.meal_set_id = ms.id
        WHERE ms.is_active = TRUE
    """)).fetchall()
    assert rows, "Chưa có meal_set nào."
    for name, set_cal, set_cost, dish_cal, dish_cost in rows:
        assert abs(float(set_cal) - float(dish_cal)) < 1.0, f"{name}: calo mâm != tổng dish"
        assert abs(float(set_cost) - float(dish_cost)) < 1.0, f"{name}: chi phí mâm != tổng dish"


def test_meal_set_dishes_json_has_no_duplicate(db_session):
    """dishes JSON len == số dish DISTINCT của set — canh gác lỗi nhân đôi CTE."""
    rows = db_session.execute(text("""
        SELECT ms.name,
               jsonb_array_length(mf.dishes) AS json_len,
               (SELECT COUNT(DISTINCT msd.dish_id) FROM meal_set_dishes msd
                 WHERE msd.meal_set_id = ms.id) AS distinct_dishes
        FROM meal_sets ms
        JOIN v_meal_sets_full mf ON mf.id = ms.id
        WHERE ms.is_active = TRUE
    """)).fetchall()
    for name, json_len, distinct_dishes in rows:
        assert json_len == distinct_dishes, (
            f"{name}: dishes JSON {json_len} phần tử nhưng {distinct_dishes} dish (nhân đôi?)."
        )


# --- Candidate provider (đọc v_meal_candidates) ---

def test_every_meal_type_has_enough_valid_candidates(db_session):
    provider = SqlMealCandidateProvider(db_session)
    counts = _valid_counts_by_type(provider.load_candidates([]))
    for meal_type in MEAL_TYPES:
        assert counts[meal_type] >= MIN_CANDIDATES_PER_SLOT, (
            f"meal_type '{meal_type}' chỉ có {counts[meal_type]} candidate hợp lệ "
            f"(cần >= {MIN_CANDIDATES_PER_SLOT})."
        )


def test_demo_exclusion_bites_but_keeps_all_slots_feasible(db_session):
    """Exclusion demo phải loại ≥1 mâm nhưng không làm rỗng meal_type nào."""
    excluded = [
        r[0] for r in db_session.execute(
            text("SELECT ingredient_id FROM user_excluded_ingredients WHERE user_id = :uid"),
            {"uid": DEMO_USER_ID},
        ).fetchall()
    ]
    assert excluded, "User demo chưa có exclusion nào."

    provider = SqlMealCandidateProvider(db_session)
    before = _valid_counts_by_type(provider.load_candidates([]))
    after = _valid_counts_by_type(provider.load_candidates(excluded))

    assert sum(after.values()) < sum(before.values()), "Exclusion demo không loại được mâm nào."
    for meal_type in MEAL_TYPES:
        assert after[meal_type] >= MIN_CANDIDATES_PER_SLOT, (
            f"Sau loại trừ demo, '{meal_type}' chỉ còn {after[meal_type]} candidate."
        )

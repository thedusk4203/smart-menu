# File: backend/app/tests/test_meal_planning/test_planner.py
# Unit test cho HeuristicPlanner (pipeline sinh thực đơn, SRS §5.3).

from datetime import date

from app.modules.meal_planning.domain import MealPlanEntity, ValidationResult
from app.modules.meal_planning.planner import HeuristicPlanner
from app.tests.test_meal_planning.factories import make_candidate, make_request

PLAN_DAY_KEYS = {"day", "date", "meals", "day_calories", "day_cost"}
MEAL_KEYS = {
    "meal_id", "name", "meal_type", "components", "calories", "protein_g",
    "fat_g", "carb_g", "cost", "dishes", "meal_set_id", "candidate_type",
}


def _basic_pool(cost=10000.0):
    return [
        make_candidate(1, meal_type="lunch", cost=cost),
        make_candidate(2, meal_type="dinner", cost=cost),
    ]


class TestGenerateFeasible:
    def test_returns_meal_plan_entity(self):
        req = make_request(days=1, meals_per_day=2, budget_limit=100000.0)
        result = HeuristicPlanner().generate(req, _basic_pool())
        assert isinstance(result, MealPlanEntity)

    def test_plan_data_structure(self):
        """D-10: cấu trúc plan_data đúng schema PlannedDay/PlannedMeal."""
        req = make_request(days=1, meals_per_day=2, budget_limit=100000.0)
        result = HeuristicPlanner().generate(req, _basic_pool())
        assert result.plan_data["meals_per_day"] == 2
        assert "warnings" in result.plan_data
        days = result.plan_data["days"]
        assert len(days) == 1
        assert set(days[0]) == PLAN_DAY_KEYS
        assert len(days[0]["meals"]) == 2
        meal = days[0]["meals"][0]
        assert set(meal) == MEAL_KEYS
        # Phase A: candidate là meal_set -> meal_id=None, dùng meal_set_id, dishes là list.
        assert meal["candidate_type"] == "meal_set"
        assert meal["meal_id"] is None
        assert meal["meal_set_id"] is not None
        assert isinstance(meal["dishes"], list)

    def test_components_are_carried_to_plan_data(self):
        req = make_request(days=1, meals_per_day=2, budget_limit=100000.0)
        pool = [
            make_candidate(
                1,
                meal_type="lunch",
                components=["Cơm trắng", "Cá kho", "Canh rau"],
            ),
            make_candidate(2, meal_type="dinner"),
        ]
        result = HeuristicPlanner().generate(req, pool)
        assert result.plan_data["days"][0]["meals"][0]["components"] == [
            "Cơm trắng", "Cá kho", "Canh rau",
        ]

    def test_slots_in_order(self):
        req = make_request(days=1, meals_per_day=2, budget_limit=100000.0)
        result = HeuristicPlanner().generate(req, _basic_pool())
        meals = result.plan_data["days"][0]["meals"]
        assert meals[0]["meal_type"] == "lunch"
        assert meals[1]["meal_type"] == "dinner"

    def test_totals_aggregated(self):
        req = make_request(days=1, meals_per_day=2, budget_limit=100000.0)
        result = HeuristicPlanner().generate(req, _basic_pool(cost=10000.0))
        assert result.total_cost == 20000
        # 2 món * 400 kcal mặc định.
        assert result.total_calories == 800


class TestStartDate:
    def test_dates_populated(self):
        req = make_request(days=2, meals_per_day=2, budget_limit=200000.0)
        pool = [
            make_candidate(1, meal_type="lunch", cost=10000.0),
            make_candidate(2, meal_type="dinner", cost=10000.0),
        ]
        result = HeuristicPlanner().generate(req, pool, start_date=date(2026, 6, 24))
        assert result.start_date == date(2026, 6, 24)
        assert result.end_date == date(2026, 6, 25)
        assert result.plan_data["days"][0]["date"] == "2026-06-24"
        assert result.plan_data["days"][1]["date"] == "2026-06-25"

    def test_no_start_date_leaves_none(self):
        req = make_request(days=1, meals_per_day=2, budget_limit=100000.0)
        result = HeuristicPlanner().generate(req, _basic_pool())
        assert result.start_date is None
        assert result.end_date is None
        assert result.plan_data["days"][0]["date"] is None


class TestExclusions:
    def test_excluded_only_option_is_infeasible(self):
        # Bữa sáng duy nhất chứa nguyên liệu bị loại -> không còn món hợp lệ.
        pool = [
            make_candidate(1, meal_type="lunch", ingredient_ids=[7]),
            make_candidate(2, meal_type="dinner", ingredient_ids=[3]),
        ]
        req = make_request(days=1, meals_per_day=2, excluded=[7], budget_limit=100000.0)
        result = HeuristicPlanner().generate(req, pool)
        assert isinstance(result, ValidationResult)
        assert result.is_feasible is False
        assert any("lunch" in r for r in result.infeasible_reasons)

    def test_excluded_avoided_when_alternative_exists(self):
        pool = [
            make_candidate(1, meal_type="lunch", ingredient_ids=[7]),   # bị loại
            make_candidate(2, meal_type="lunch", ingredient_ids=[3]),   # hợp lệ
            make_candidate(3, meal_type="dinner", ingredient_ids=[4]),
        ]
        req = make_request(days=1, meals_per_day=2, excluded=[7], budget_limit=100000.0)
        result = HeuristicPlanner().generate(req, pool)
        assert isinstance(result, MealPlanEntity)
        lunch = result.plan_data["days"][0]["meals"][0]
        assert lunch["meal_set_id"] == 2


class TestBudget:
    def test_unlimited_budget_allows_expensive_meals(self):
        """D-01 regression: budget_limit=None -> sinh được thực đơn dù món rất đắt."""
        pool = [
            make_candidate(1, meal_type="lunch", cost=9_000_000.0),
            make_candidate(2, meal_type="dinner", cost=9_000_000.0),
        ]
        req = make_request(days=1, meals_per_day=2, budget_limit=None)
        result = HeuristicPlanner().generate(req, pool)
        assert isinstance(result, MealPlanEntity)
        assert result.total_cost == 18_000_000

    def test_budget_too_low_is_infeasible(self):
        pool = _basic_pool(cost=50000.0)
        req = make_request(days=1, meals_per_day=2, budget_limit=1000.0)
        result = HeuristicPlanner().generate(req, pool)
        assert isinstance(result, ValidationResult)
        assert result.is_feasible is False
        assert any("ngân sách" in r.lower() for r in result.infeasible_reasons)


class TestVariety:
    def test_alternates_repeated_meals_across_days(self):
        # 2 bữa trưa tương đương + 1 bữa tối: planner nên đổi bữa trưa sang ngày 2.
        pool = [
            make_candidate(1, meal_type="lunch", cost=10000.0),
            make_candidate(2, meal_type="lunch", cost=10000.0),
            make_candidate(3, meal_type="dinner", cost=10000.0),
        ]
        req = make_request(days=2, meals_per_day=2, budget_limit=200000.0)
        result = HeuristicPlanner().generate(req, pool)
        assert isinstance(result, MealPlanEntity)
        lunch_day1 = result.plan_data["days"][0]["meals"][0]["meal_set_id"]
        lunch_day2 = result.plan_data["days"][1]["meals"][0]["meal_set_id"]
        assert lunch_day1 != lunch_day2


class TestRegenerateSeed:
    """FR-PLAN-05: 'tạo lại thực đơn' — seed cho phép ra phương án khác nhau
    nhưng vẫn tái lập được, và không seed thì vẫn deterministic như cũ."""

    def _pool(self):
        # Nhiều lựa chọn tương đương cho mỗi bữa -> có 'top-K' để xáo trộn.
        return [
            make_candidate(1, meal_type="lunch", cost=10000.0),
            make_candidate(2, meal_type="lunch", cost=10000.0),
            make_candidate(3, meal_type="lunch", cost=10000.0),
            make_candidate(4, meal_type="dinner", cost=10000.0),
            make_candidate(5, meal_type="dinner", cost=10000.0),
            make_candidate(6, meal_type="dinner", cost=10000.0),
        ]

    def test_same_seed_is_reproducible(self):
        req = make_request(days=1, meals_per_day=2, budget_limit=100000.0)
        a = HeuristicPlanner().generate(req, self._pool(), seed=42)
        b = HeuristicPlanner().generate(req, self._pool(), seed=42)
        assert a.plan_data == b.plan_data

    def test_different_seeds_can_produce_different_plans(self):
        req = make_request(days=1, meals_per_day=2, budget_limit=100000.0)
        lunch_picks = set()
        for s in range(10):
            result = HeuristicPlanner().generate(req, self._pool(), seed=s)
            lunch_picks.add(result.plan_data["days"][0]["meals"][0]["meal_set_id"])
        assert len(lunch_picks) > 1

    def test_no_seed_stays_deterministic(self):
        req = make_request(days=1, meals_per_day=2, budget_limit=100000.0)
        a = HeuristicPlanner().generate(req, self._pool())
        b = HeuristicPlanner().generate(req, self._pool())
        assert a.plan_data == b.plan_data

# File: backend/app/tests/test_meal_planning/test_constraint_checker.py
# Unit test cho hard-constraint checker (SRS §5.4).

from app.modules.meal_planning import constraint_checker as cc
from app.tests.test_meal_planning.factories import make_candidate, make_request


# ---------------------------------------------------------------------------
# slots_for
# ---------------------------------------------------------------------------

class TestSlotsFor:
    def test_two_meals(self):
        assert cc.slots_for(2) == ["breakfast", "dinner"]

    def test_three_meals(self):
        assert cc.slots_for(3) == ["breakfast", "lunch", "dinner"]

    def test_unknown_falls_back_to_three(self):
        # Giá trị lạ -> mặc định 3 bữa (an toàn cho MVP).
        assert cc.slots_for(5) == ["breakfast", "lunch", "dinner"]


# ---------------------------------------------------------------------------
# has_excluded_ingredient (D-07: nhận set đã dựng sẵn)
# ---------------------------------------------------------------------------

class TestHasExcludedIngredient:
    def test_empty_excluded_returns_false(self):
        c = make_candidate(1, ingredient_ids=[10, 20])
        assert cc.has_excluded_ingredient(c, set()) is False

    def test_match_returns_true(self):
        c = make_candidate(1, ingredient_ids=[10, 20])
        assert cc.has_excluded_ingredient(c, {20}) is True

    def test_no_match_returns_false(self):
        c = make_candidate(1, ingredient_ids=[10, 20])
        assert cc.has_excluded_ingredient(c, {99}) is False


# ---------------------------------------------------------------------------
# has_valid_data (HC-07)
# ---------------------------------------------------------------------------

class TestHasValidData:
    def test_valid(self):
        assert cc.has_valid_data(make_candidate(1, cost=1000.0, calories=300.0)) is True

    def test_zero_cost_invalid(self):
        assert cc.has_valid_data(make_candidate(1, cost=0.0, calories=300.0)) is False

    def test_zero_calories_invalid(self):
        assert cc.has_valid_data(make_candidate(1, cost=1000.0, calories=0.0)) is False


# ---------------------------------------------------------------------------
# candidate_is_eligible
# ---------------------------------------------------------------------------

class TestCandidateIsEligible:
    def test_eligible(self):
        c = make_candidate(1, meal_type="breakfast", ingredient_ids=[1])
        assert cc.candidate_is_eligible(c, "breakfast", set()) is True

    def test_wrong_slot(self):
        c = make_candidate(1, meal_type="dinner")
        assert cc.candidate_is_eligible(c, "breakfast", set()) is False

    def test_excluded_ingredient(self):
        c = make_candidate(1, meal_type="breakfast", ingredient_ids=[7])
        assert cc.candidate_is_eligible(c, "breakfast", {7}) is False

    def test_invalid_data(self):
        c = make_candidate(1, meal_type="breakfast", cost=0.0)
        assert cc.candidate_is_eligible(c, "breakfast", set()) is False


# ---------------------------------------------------------------------------
# validate_plan
# ---------------------------------------------------------------------------

class TestValidatePlan:
    def _valid_two_meal_day(self):
        return [
            make_candidate(1, meal_type="breakfast", cost=10000.0),
            make_candidate(2, meal_type="dinner", cost=10000.0),
        ]

    def test_valid_plan(self):
        req = make_request(days=1, meals_per_day=2, budget_limit=100000.0)
        result = cc.validate_plan([self._valid_two_meal_day()], req)
        assert result.status == "valid"
        assert result.is_feasible is True

    def test_wrong_day_count_hc04(self):
        req = make_request(days=2, meals_per_day=2, budget_limit=100000.0)
        result = cc.validate_plan([self._valid_two_meal_day()], req)  # chỉ 1 ngày
        assert result.status == "infeasible"
        assert any("HC-04" in v for v in result.hard_violations)

    def test_wrong_meals_per_day_hc05(self):
        req = make_request(days=1, meals_per_day=2, budget_limit=100000.0)
        one_meal_day = [make_candidate(1, meal_type="breakfast")]
        result = cc.validate_plan([one_meal_day], req)
        assert result.status == "infeasible"
        assert any("HC-05" in v for v in result.hard_violations)

    def test_budget_exceeded_hc01(self):
        req = make_request(days=1, meals_per_day=2, budget_limit=5000.0)
        result = cc.validate_plan([self._valid_two_meal_day()], req)  # tổng 20000 > 5000
        assert result.status == "infeasible"
        assert any("HC-01" in v for v in result.hard_violations)

    def test_budget_none_skips_hc01(self):
        """D-01 regression: budget_limit=None nghĩa là KHÔNG giới hạn -> không
        bao giờ vi phạm HC-01 dù chi phí lớn."""
        req = make_request(days=1, meals_per_day=2, budget_limit=None)
        expensive = [
            make_candidate(1, meal_type="breakfast", cost=9_000_000.0),
            make_candidate(2, meal_type="dinner", cost=9_000_000.0),
        ]
        result = cc.validate_plan([expensive], req)
        assert result.status == "valid"
        assert not any("HC-01" in v for v in result.hard_violations)

    def test_excluded_ingredient_in_plan_hc02(self):
        req = make_request(days=1, meals_per_day=2, budget_limit=100000.0, excluded=[7])
        day = [
            make_candidate(1, meal_type="breakfast", ingredient_ids=[7]),
            make_candidate(2, meal_type="dinner", ingredient_ids=[3]),
        ]
        result = cc.validate_plan([day], req)
        assert result.status == "infeasible"
        assert any("HC-02/03" in v for v in result.hard_violations)

    def test_wrong_slot_order_hc06(self):
        req = make_request(days=1, meals_per_day=2, budget_limit=100000.0)
        # slot 0 cần breakfast nhưng đặt dinner.
        day = [
            make_candidate(1, meal_type="dinner", cost=10000.0),
            make_candidate(2, meal_type="dinner", cost=10000.0),
        ]
        result = cc.validate_plan([day], req)
        assert result.status == "infeasible"
        assert any("HC-06" in v for v in result.hard_violations)

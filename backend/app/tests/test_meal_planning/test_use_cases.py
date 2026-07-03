# File: backend/app/tests/test_meal_planning/test_use_cases.py
# Unit test cho BuildPlanRequestUseCase (chuẩn hóa request) và
# GenerateMealPlanUseCase (orchestration) — dùng fake repo/port, không cần DB.

import pytest

from app.modules.meal_planning.domain import MealPlanEntity, ValidationResult
from app.modules.meal_planning.exceptions import (
    IncompleteProfileError,
    InfeasibleNutritionError,
)
from app.modules.meal_planning.ports import (
    MealCandidateProviderPort,
    MealPlannerPort,
)
from app.modules.meal_planning.use_cases import (
    BuildPlanRequestUseCase,
    GenerateMealPlanUseCase,
)
from app.modules.profiles.domain import ExcludedIngredientEntity, UserProfileEntity
from app.modules.profiles.exceptions import ProfileNotFoundError
from app.modules.profiles.ports import ExclusionRepositoryPort, UserProfileRepositoryPort
from app.shared.enums import ActivityLevel, FitnessGoal, Gender
from app.tests.test_meal_planning.factories import make_candidate, make_request


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------

class _FakeProfileRepo(UserProfileRepositoryPort):
    def __init__(self, profile):
        self._profile = profile

    def get_by_user(self, user_id):
        return self._profile

    def create_empty(self, user_id, full_name=None):  # pragma: no cover - không dùng
        raise NotImplementedError

    def save(self, profile):  # pragma: no cover - không dùng
        raise NotImplementedError


class _FakeExclusionRepo(ExclusionRepositoryPort):
    def __init__(self, items=None):
        self._items = items or []

    def list_by_user(self, user_id):
        return list(self._items)

    def get(self, user_id, ingredient_id):  # pragma: no cover
        raise NotImplementedError

    def add(self, item):  # pragma: no cover
        raise NotImplementedError

    def remove(self, user_id, ingredient_id):  # pragma: no cover
        raise NotImplementedError


class _FakeCandidateProvider(MealCandidateProviderPort):
    def __init__(self, candidates):
        self._candidates = candidates
        self.received_excluded = None

    def load_candidates(self, excluded_ingredient_ids):
        self.received_excluded = excluded_ingredient_ids
        return list(self._candidates)


class _RecordingPlanner(MealPlannerPort):
    """Planner giả (D-19) — ghi lại lời gọi, trả kết quả định sẵn."""

    def __init__(self, result):
        self._result = result
        self.calls = []

    def generate(self, request, candidates, *, start_date=None, seed=None):
        self.calls.append((request, candidates, start_date, seed))
        return self._result


def _complete_profile(**overrides):
    base = dict(
        user_id=1,
        gender=Gender.MALE,
        age=25,
        height_cm=175.0,
        weight_kg=70.0,
        activity_level=ActivityLevel.MODERATE,
        goal=FitnessGoal.MAINTAIN,
        meals_per_day=3,
        daily_budget=None,
    )
    base.update(overrides)
    return UserProfileEntity(**base)


# ---------------------------------------------------------------------------
# BuildPlanRequestUseCase
# ---------------------------------------------------------------------------

class TestBuildPlanRequest:
    def _use_case(self, profile, exclusions=None):
        return BuildPlanRequestUseCase(
            _FakeProfileRepo(profile), _FakeExclusionRepo(exclusions)
        )

    def test_profile_not_found(self):
        uc = self._use_case(None)
        with pytest.raises(ProfileNotFoundError):
            uc.execute(user_id=1)

    def test_incomplete_profile_raises(self):
        """D-02: thiếu cân nặng -> IncompleteProfileError (422), không vỡ 500."""
        uc = self._use_case(_complete_profile(weight_kg=None))
        with pytest.raises(IncompleteProfileError, match="cân nặng"):
            uc.execute(user_id=1)

    def test_infeasible_target_raises(self):
        """D-02: hồ sơ cho mục tiêu calo < ngưỡng an toàn -> InfeasibleNutritionError."""
        infeasible = _complete_profile(
            gender=Gender.FEMALE, age=50, weight_kg=45.0, height_cm=155.0,
            activity_level=ActivityLevel.SEDENTARY, goal=FitnessGoal.LOSE_WEIGHT,
        )
        uc = self._use_case(infeasible)
        with pytest.raises(InfeasibleNutritionError):
            uc.execute(user_id=1)

    def test_no_budget_anywhere_is_none(self):
        """D-01: không có ngân sách -> budget_limit=None (không giới hạn), KHÔNG 0."""
        uc = self._use_case(_complete_profile(daily_budget=None))
        req = uc.execute(user_id=1)
        assert req.budget_limit is None

    def test_daily_budget_scaled_to_period(self):
        uc = self._use_case(_complete_profile(daily_budget=50000.0))
        req = uc.execute(user_id=1, days=7)
        assert req.budget_limit == 50000.0 * 7

    def test_api_budget_used_as_is(self):
        uc = self._use_case(_complete_profile(daily_budget=50000.0))
        req = uc.execute(user_id=1, days=7, budget_limit=120000.0)
        assert req.budget_limit == 120000.0

    def test_defaults_days_and_meals_per_day(self):
        uc = self._use_case(_complete_profile(meals_per_day=2))
        req = uc.execute(user_id=1)
        assert req.days == BuildPlanRequestUseCase.DEFAULT_DAYS
        assert req.meals_per_day == 2

    def test_exclusions_gathered(self):
        exclusions = [
            ExcludedIngredientEntity(id=1, user_id=1, ingredient_id=7, reason="allergy"),
            ExcludedIngredientEntity(id=2, user_id=1, ingredient_id=9, reason="dislike"),
        ]
        uc = self._use_case(_complete_profile(), exclusions)
        req = uc.execute(user_id=1)
        assert set(req.excluded_ingredient_ids) == {7, 9}


# ---------------------------------------------------------------------------
# GenerateMealPlanUseCase
# ---------------------------------------------------------------------------

class TestGenerateMealPlan:
    def test_passes_excluded_to_provider_and_returns_plan(self):
        provider = _FakeCandidateProvider([make_candidate(1, meal_type="breakfast")])
        plan = MealPlanEntity(id=None, user_id=1)
        planner = _RecordingPlanner(plan)
        uc = GenerateMealPlanUseCase(provider, planner)

        req = make_request(excluded=[7, 8])
        result = uc.execute(req)

        assert result is plan
        assert provider.received_excluded == [7, 8]
        assert len(planner.calls) == 1

    def test_injected_planner_used(self):
        """D-19: use case nhận MealPlannerPort -> có thể inject planner giả."""
        provider = _FakeCandidateProvider([])
        infeasible = ValidationResult(status="infeasible", infeasible_reasons=["x"])
        planner = _RecordingPlanner(infeasible)
        uc = GenerateMealPlanUseCase(provider, planner)

        result = uc.execute(make_request())
        assert isinstance(result, ValidationResult)
        assert result.is_feasible is False

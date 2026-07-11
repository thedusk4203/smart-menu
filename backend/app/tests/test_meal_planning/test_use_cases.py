# File: backend/app/tests/test_meal_planning/test_use_cases.py
# Unit test cho BuildPlanRequestUseCase (chuẩn hóa request) và
# GenerateMealPlanUseCase (orchestration) — dùng fake repo/port, không cần DB.

from datetime import date

import pytest

from app.modules.meal_planning.domain import MealPlanEntity, ValidationResult
from app.modules.meal_planning.exceptions import (
    IncompleteProfileError,
    InfeasibleNutritionError,
    InvalidMealSelectionError,
)
from app.modules.meal_planning.ports import (
    MealCandidateProviderPort,
    MealPlanRepositoryPort,
    MealPlannerPort,
)
from app.modules.meal_planning.schemas import MealPlanCreate, SavedMealSlot, SavedPlanDay
from app.modules.meal_planning.use_cases import (
    BuildPlanRequestUseCase,
    GenerateMealPlanUseCase,
    SaveMealPlanUseCase,
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

    def load_by_ids(self, meal_set_ids):
        by = {c.meal_id: c for c in self._candidates}
        return {i: by[i] for i in meal_set_ids if i in by}


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


# ---------------------------------------------------------------------------
# SaveMealPlanUseCase (Gate 0 — recompute, chống tamper)
# ---------------------------------------------------------------------------

class _FakeMealPlanRepo(MealPlanRepositoryPort):
    def __init__(self):
        self.created = None

    def create(self, plan):
        self.created = plan
        return plan

    def list_by_user(self, user_id):  # pragma: no cover
        return []

    def get(self, plan_id):  # pragma: no cover
        return None

    def delete(self, plan_id):  # pragma: no cover
        pass


def _save_data(days_pairs, *, start=date(2026, 6, 1), name="Tuần"):
    """days_pairs: list các ngày, mỗi ngày là list (slot, meal_set_id)."""
    days = [
        SavedPlanDay(day=i + 1, meals=[SavedMealSlot(slot=s, meal_set_id=mid) for s, mid in day])
        for i, day in enumerate(days_pairs)
    ]
    return MealPlanCreate(name=name, start_date=start, days=days)


class TestSaveMealPlan:
    def _uc(self, candidates):
        repo = _FakeMealPlanRepo()
        return SaveMealPlanUseCase(repo, _FakeCandidateProvider(candidates)), repo

    def test_recomputes_totals_from_authoritative_candidates(self):
        cands = [
            make_candidate(1, meal_type="lunch", cost=30000.0, calories=700.0),
            make_candidate(2, meal_type="dinner", cost=20000.0, calories=650.0),
        ]
        uc, repo = self._uc(cands)
        result = uc.execute(_save_data([[("lunch", 1), ("dinner", 2)]]), user_id=99)
        assert result is repo.created
        assert result.user_id == 99                 # từ JWT, không phải client
        assert result.total_cost == 50000           # Σ cost thật; client không gửi được
        assert result.total_calories == 1350.0
        meals = result.plan_data["days"][0]["meals"]
        assert [m["meal_set_id"] for m in meals] == [1, 2]
        assert all(m["candidate_type"] == "meal_set" and m["meal_id"] is None for m in meals)

    def test_rejects_unknown_meal_set_id(self):
        uc, _ = self._uc([make_candidate(1, meal_type="lunch")])
        with pytest.raises(InvalidMealSelectionError):
            uc.execute(_save_data([[("lunch", 1), ("dinner", 999)]]), user_id=1)

    def test_rejects_slot_mismatch(self):
        uc, _ = self._uc([make_candidate(1, meal_type="lunch")])
        with pytest.raises(InvalidMealSelectionError):
            uc.execute(_save_data([[("dinner", 1)]]), user_id=1)

    def test_empty_plan_rejected(self):
        uc, _ = self._uc([make_candidate(1, meal_type="lunch")])
        with pytest.raises(InvalidMealSelectionError):
            uc.execute(_save_data([]), user_id=1)

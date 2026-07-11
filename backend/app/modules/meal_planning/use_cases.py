from __future__ import annotations

from dataclasses import replace
from datetime import date
from zoneinfo import ZoneInfo
from types import SimpleNamespace

from app.core.exceptions import ValidationAppError
from app.modules.meal_planning import constraint_checker
from app.modules.meal_planning.composition import slots_for
from app.modules.meal_planning.domain import ComposedMeal, MealPlanEntity, PlanRequest, ValidationResult
from app.modules.meal_planning.exceptions import (
    IncompleteProfileError,
    InfeasibleNutritionError,
    InvalidMealSelectionError,
    MealPlanNotFoundError,
)
from app.modules.meal_planning.planner import DishPlanner
from app.modules.meal_planning.ports import (
    DishCandidateProviderPort,
    MealPlannerPort,
    MealPlanRepositoryPort,
)
from app.modules.meal_planning.schemas import MealPlanCreate
from app.modules.nutrition.calculator import NutritionCalculator
from app.modules.profiles.exceptions import ProfileNotFoundError
from app.modules.profiles.ports import ExclusionRepositoryPort, UserProfileRepositoryPort


class SaveMealPlanUseCase:
    """Lưu selection dish bằng cách reload và dựng lại snapshot V2 ở backend."""

    def __init__(
        self,
        repo: MealPlanRepositoryPort,
        candidate_provider: DishCandidateProviderPort,
        build_request: "BuildPlanRequestUseCase",
    ) -> None:
        self._repo = repo
        self._candidates = candidate_provider
        self._build_request = build_request
        self._snapshot_builder = DishPlanner()

    def execute(self, data: MealPlanCreate, *, user_id: int) -> MealPlanEntity:
        first_slots = tuple(meal.slot for meal in data.days[0].meals)
        try:
            expected_slots = slots_for(len(first_slots))
        except ValueError as error:
            raise InvalidMealSelectionError(str(error)) from error
        if first_slots != expected_slots or any(
            tuple(meal.slot for meal in day.meals) != expected_slots for day in data.days
        ):
            raise InvalidMealSelectionError(
                "slot phải theo đúng thứ tự lunch,dinner hoặc breakfast,lunch,dinner cho mọi ngày"
            )
        dish_ids = [dish_id for day in data.days for meal in day.meals for dish_id in meal.dish_ids]
        by_id = self._candidates.load_by_ids(dish_ids)
        missing = sorted({dish_id for dish_id in dish_ids if dish_id not in by_id})
        if missing:
            raise InvalidMealSelectionError(
                f"dish không tồn tại, không active hoặc chưa planner-ready: {missing}"
            )
        request = self._build_request.execute(
            user_id,
            days=len(data.days),
            meals_per_day=len(expected_slots),
            budget_limit=data.budget_limit,
        )
        composed_days = [
            [
                ComposedMeal(slot=selection.slot, dishes=tuple(by_id[dish_id] for dish_id in selection.dish_ids))
                for selection in day.meals
            ]
            for day in data.days
        ]
        validation = constraint_checker.validate_plan(composed_days, request)
        if not validation.is_feasible:
            raise InvalidMealSelectionError("; ".join(validation.hard_violations))
        entity = self._snapshot_builder.build_entity(
            composed_days,
            request,
            data.start_date,
            [],
            SimpleNamespace(solver_time_ms=0, nutrition_score=0, solver_status="manual_selection"),
        )
        # Keep the fallback consistent for API clients that do not provide a name.
        from datetime import datetime
        name = data.name or f"Thực đơn {datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')).strftime('%H:%M %d/%m/%Y')}"
        return self._repo.create(replace(entity, name=name))


class ListMealPlansUseCase:
    def __init__(self, repo: MealPlanRepositoryPort) -> None:
        self._repo = repo

    def execute(self, user_id: int) -> list[MealPlanEntity]:
        return self._repo.list_by_user(user_id)


class GetMealPlanUseCase:
    def __init__(self, repo: MealPlanRepositoryPort) -> None:
        self._repo = repo

    def execute(self, plan_id: int) -> MealPlanEntity:
        plan = self._repo.get(plan_id)
        if plan is None:
            raise MealPlanNotFoundError(plan_id)
        return plan


class DeleteMealPlanUseCase:
    def __init__(self, repo: MealPlanRepositoryPort) -> None:
        self._repo = repo

    def execute(self, plan_id: int) -> None:
        if self._repo.get(plan_id) is None:
            raise MealPlanNotFoundError(plan_id)
        self._repo.delete(plan_id)


class GenerateMealPlanUseCase:
    def __init__(
        self,
        candidate_provider: DishCandidateProviderPort,
        planner: MealPlannerPort | None = None,
    ) -> None:
        self._candidates = candidate_provider
        self._planner = planner or DishPlanner()

    def execute(
        self,
        request: PlanRequest,
        *,
        start_date: date | None = None,
        seed: int | None = None,
    ) -> MealPlanEntity | ValidationResult:
        candidates = self._candidates.load_candidates(request.excluded_ingredient_ids)
        return self._planner.generate(request, candidates, start_date=start_date, seed=seed)


class BuildPlanRequestUseCase:
    DEFAULT_DAYS = 7

    def __init__(
        self,
        profile_repo: UserProfileRepositoryPort,
        exclusion_repo: ExclusionRepositoryPort,
    ) -> None:
        self._profiles = profile_repo
        self._exclusions = exclusion_repo

    def execute(
        self,
        user_id: int,
        *,
        days: int | None = None,
        meals_per_day: int | None = None,
        budget_limit: float | None = None,
        preferred_tags: list[str] | None = None,
        previous_plan_signature: str | None = None,
    ) -> PlanRequest:
        profile = self._profiles.get_by_user(user_id)
        if profile is None:
            raise ProfileNotFoundError(user_id)
        missing = [
            label
            for label, value in (
                ("giới tính", profile.gender),
                ("tuổi", profile.age),
                ("chiều cao", profile.height_cm),
                ("cân nặng", profile.weight_kg),
            )
            if value is None
        ]
        if missing:
            raise IncompleteProfileError(missing)
        target = NutritionCalculator.calculate_nutrition_target(
            gender=profile.gender,
            age=profile.age,
            weight_kg=profile.weight_kg,
            height_cm=profile.height_cm,
            activity_level=profile.activity_level,
            fitness_goal=profile.goal,
        )
        if not target.is_feasible:
            raise InfeasibleNutritionError([warning.message for warning in target.warnings])
        resolved_days = days or self.DEFAULT_DAYS
        resolved_mpd = meals_per_day or profile.meals_per_day
        if not 1 <= resolved_days <= 7 or resolved_mpd not in (2, 3):
            raise ValidationAppError("days phải từ 1–7 và meals_per_day phải là 2 hoặc 3")
        if budget_limit is not None and budget_limit <= 0:
            raise ValidationAppError("budget_limit phải lớn hơn 0")
        if budget_limit is not None:
            resolved_budget: float | None = float(budget_limit)
        elif profile.daily_budget is not None:
            resolved_budget = float(profile.daily_budget) * resolved_days
        else:
            resolved_budget = None
        tags: list[str] = []
        seen: set[str] = set()
        for tag in preferred_tags or []:
            normalized = " ".join(tag.split())
            if normalized and normalized.casefold() not in seen:
                tags.append(normalized)
                seen.add(normalized.casefold())
        excluded = list({exclusion.ingredient_id for exclusion in self._exclusions.list_by_user(user_id)})
        return PlanRequest(
            user_id=user_id,
            days=resolved_days,
            meals_per_day=resolved_mpd,
            budget_limit=resolved_budget,
            target_calories=float(target.target_calories),
            target_protein_g=target.daily_protein_g,
            target_fat_g=target.daily_fat_g,
            target_carb_g=target.daily_carb_g,
            excluded_ingredient_ids=excluded,
            preferred_tags=tags,
            previous_plan_signature=previous_plan_signature,
        )

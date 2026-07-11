from __future__ import annotations

from dataclasses import asdict
from datetime import date, timedelta

from app.modules.meal_planning.domain import (
    MealPlanEntity,
    PlannedDay,
    PlannedMeal,
    PlanRequest,
    ValidationResult,
)
from app.modules.meal_planning.exceptions import (
    IncompleteProfileError,
    InfeasibleNutritionError,
    InvalidMealSelectionError,
    MealPlanNotFoundError,
)
from app.modules.meal_planning.planner import HeuristicPlanner
from app.modules.meal_planning.ports import (
    MealCandidateProviderPort,
    MealPlannerPort,
    MealPlanRepositoryPort,
)
from app.modules.meal_planning.schemas import MealPlanCreate
from app.modules.nutrition.calculator import NutritionCalculator
from app.modules.profiles.exceptions import ProfileNotFoundError
from app.modules.profiles.ports import ExclusionRepositoryPort, UserProfileRepositoryPort


class SaveMealPlanUseCase:
    """Lưu thực đơn từ lựa chọn của client (id mâm cơm theo ngày/slot). Reload
    dữ liệu mâm cơm từ nguồn đúng (v_meal_candidates) rồi RECOMPUTE totals +
    plan_data — không tin total_cost/total_calories/plan_data client gửi."""

    def __init__(
        self,
        repo: MealPlanRepositoryPort,
        candidate_provider: MealCandidateProviderPort,
    ) -> None:
        self._repo = repo
        self._candidates = candidate_provider

    def execute(self, data: MealPlanCreate, *, user_id: int) -> MealPlanEntity:
        ids = [m.meal_set_id for d in data.days for m in d.meals]
        if not ids:
            raise InvalidMealSelectionError("thực đơn không có bữa nào")

        by_id = self._candidates.load_by_ids(ids)
        missing = sorted({i for i in ids if i not in by_id})
        if missing:
            raise InvalidMealSelectionError(
                f"mâm cơm không tồn tại hoặc không khả dụng: {missing}"
            )

        plan_days: list[dict] = []
        total_cost = 0.0
        total_calories = 0.0
        max_meals = 0
        for d in data.days:
            day_meals: list[PlannedMeal] = []
            day_cost = 0.0
            day_cal = 0.0
            for m in d.meals:
                c = by_id[m.meal_set_id]
                if c.meal_type != m.slot:
                    raise InvalidMealSelectionError(
                        f"mâm '{c.name}' là bữa '{c.meal_type}', không khớp slot '{m.slot}'"
                    )
                day_meals.append(PlannedMeal(
                    meal_id=None,
                    name=c.name,
                    meal_type=c.meal_type,
                    components=list(c.components),
                    calories=round(c.total_calories, 1),
                    protein_g=round(c.total_protein_g, 1),
                    fat_g=round(c.total_fat_g, 1),
                    carb_g=round(c.total_carb_g, 1),
                    cost=round(c.estimated_cost, 0),
                    dishes=list(c.dishes),
                    meal_set_id=c.meal_id,
                    candidate_type="meal_set",
                ))
                day_cost += c.estimated_cost
                day_cal += c.total_calories
            day_date = (data.start_date + timedelta(days=d.day - 1)).isoformat()
            plan_days.append(asdict(PlannedDay(
                day=d.day,
                date=day_date,
                meals=day_meals,
                day_calories=round(day_cal, 1),
                day_cost=round(day_cost, 0),
            )))
            total_cost += day_cost
            total_calories += day_cal
            max_meals = max(max_meals, len(day_meals))

        end_date = data.start_date + timedelta(days=len(data.days) - 1)
        entity = MealPlanEntity(
            id=None,
            user_id=user_id,
            name=data.name,
            start_date=data.start_date,
            end_date=end_date,
            budget_limit=data.budget_limit,
            total_cost=round(total_cost, 0),
            total_calories=round(total_calories, 1),
            plan_data={"days": plan_days, "warnings": [], "meals_per_day": max_meals},
        )
        return self._repo.create(entity)


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
        candidate_provider: MealCandidateProviderPort,
        planner: MealPlannerPort | None = None,
    ) -> None:
        self._candidates = candidate_provider
        self._planner = planner or HeuristicPlanner()

    def execute(
        self,
        request: PlanRequest,
        *,
        start_date: date | None = None,
        seed: int | None = None,
    ) -> MealPlanEntity | ValidationResult:
        # seed truyền xuống planner để hỗ trợ "tạo lại thực đơn khác" (FR-PLAN-05).
        candidates = self._candidates.load_candidates(request.excluded_ingredient_ids)
        return self._planner.generate(request, candidates, start_date=start_date, seed=seed)


class BuildPlanRequestUseCase:
    DEFAULT_DAYS = 7  # MVP mặc định 7 ngày (HC-04)

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
    ) -> PlanRequest:
        profile = self._profiles.get_by_user(user_id)
        if profile is None:
            raise ProfileNotFoundError(user_id)

        # Hồ sơ phải đủ trường để tính dinh dưỡng — nếu thiếu, báo rõ thay vì
        # để NutritionCalculator vỡ thành lỗi 500 mơ hồ (review D-02).
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

        # Mục tiêu dinh dưỡng/ngày — tính deterministic từ hồ sơ.
        target = NutritionCalculator.calculate_nutrition_target(
            gender=profile.gender,
            age=profile.age,
            weight_kg=profile.weight_kg,
            height_cm=profile.height_cm,
            activity_level=profile.activity_level,
            fitness_goal=profile.goal,
        )

        # Mục tiêu bất khả thi (calo < ngưỡng an toàn) -> KHÔNG sinh thực đơn
        # theo mục tiêu vô nghĩa; báo lý do kèm cảnh báo (review D-02).
        if not target.is_feasible:
            raise InfeasibleNutritionError([w.message for w in target.warnings])

        # Loại trừ = dị ứng + không ăn (gộp toàn bộ exclusion của user).
        excluded = [e.ingredient_id for e in self._exclusions.list_by_user(user_id)]

        resolved_days = days or self.DEFAULT_DAYS
        resolved_mpd = meals_per_day or profile.meals_per_day

        # Ngân sách: ưu tiên giá trị API truyền (đã là cả kỳ). Nếu lấy từ hồ sơ
        # (daily_budget = ngân sách/ngày) thì quy ra cả kỳ. Không có ngân sách
        # nào -> None = KHÔNG giới hạn (review D-01), KHÔNG phải 0 (chặn mọi món).
        if budget_limit is not None:
            resolved_budget: float | None = float(budget_limit)
        elif profile.daily_budget is not None:
            resolved_budget = float(profile.daily_budget) * resolved_days
        else:
            resolved_budget = None

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
            preferred_tags=preferred_tags or [],
        )

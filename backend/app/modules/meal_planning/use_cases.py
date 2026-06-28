# File: backend/app/modules/meal_planning/use_cases.py
#
# NOTE: chứa use case cho việc LƯU/ĐỌC thực đơn (API cơ bản — Bình) và use
# case SINH thực đơn tự động (GenerateMealPlanUseCase — Đức), gọi planner +
# scorer + constraint_checker qua MealCandidateProviderPort.
from __future__ import annotations

from datetime import date

from app.modules.meal_planning.domain import MealPlanEntity, PlanRequest, ValidationResult
from app.modules.meal_planning.exceptions import (
    IncompleteProfileError,
    InfeasibleNutritionError,
    MealPlanNotFoundError,
)
from app.modules.meal_planning.planner import HeuristicPlanner
from app.modules.meal_planning.ports import (
    MealCandidateProviderPort,
    MealPlannerPort,
    MealPlanRepositoryPort,
)
from app.modules.nutrition.calculator import NutritionCalculator
from app.modules.profiles.exceptions import ProfileNotFoundError
from app.modules.profiles.ports import ExclusionRepositoryPort, UserProfileRepositoryPort


class SaveMealPlanUseCase:
    def __init__(self, repo: MealPlanRepositoryPort) -> None:
        self._repo = repo

    def execute(self, plan: MealPlanEntity) -> MealPlanEntity:
        return self._repo.create(plan)


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
    """Sinh thực đơn tự động từ một PlanRequest đã chuẩn hóa.

    Orchestration thuần: tải candidate qua port (đã loại trừ nguyên liệu dị
    ứng/không ăn), rồi giao cho HeuristicPlanner. Trả về MealPlanEntity (chưa
    lưu — client gọi POST /api/meal-plans nếu muốn lưu) hoặc ValidationResult
    nếu bất khả thi. KHÔNG tự lưu để giữ tách bạch giữa "sinh" và "lưu"."""

    def __init__(
        self,
        candidate_provider: MealCandidateProviderPort,
        planner: MealPlannerPort | None = None,
    ) -> None:
        self._candidates = candidate_provider
        self._planner = planner or HeuristicPlanner()

    def execute(
        self, request: PlanRequest, *, start_date: date | None = None
    ) -> MealPlanEntity | ValidationResult:
        candidates = self._candidates.load_candidates(request.excluded_ingredient_ids)
        return self._planner.generate(request, candidates, start_date=start_date)


class BuildPlanRequestUseCase:
    """Chuẩn hóa input thô từ API/form thành PlanRequest (bước 1-3 SRS §5.3).

    Tập hợp dữ liệu nằm rải rác ở nhiều module — hồ sơ + mục tiêu dinh dưỡng
    (nutrition) và danh sách loại trừ (profiles) — để router không phải chứa
    logic nghiệp vụ. Mục tiêu dinh dưỡng tính bằng NutritionCalculator
    (deterministic) từ hồ sơ; ngân sách/số bữa mặc định lấy từ hồ sơ nếu API
    không truyền."""

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

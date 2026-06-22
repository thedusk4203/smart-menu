# File: backend/app/modules/meal_planning/use_cases.py
#
# NOTE: chỉ chứa use case cho việc LƯU/ĐỌC thực đơn (API cơ bản — phụ trách
# bởi Bình). Use case sinh thực đơn tự động (gọi planner + scorer +
# constraint_checker) sẽ do Đức bổ sung tại đây, ví dụ
# `class GenerateMealPlanUseCase`, khi triển khai phần thuật toán.
from __future__ import annotations

from app.modules.meal_planning.domain import MealPlanEntity
from app.modules.meal_planning.exceptions import MealPlanNotFoundError
from app.modules.meal_planning.ports import MealPlanRepositoryPort


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

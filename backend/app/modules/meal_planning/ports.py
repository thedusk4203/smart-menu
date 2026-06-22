# File: backend/app/modules/meal_planning/ports.py
#
# NOTE: chỉ định nghĩa port cho phần lưu trữ (storage). Port cho phần sinh
# thực đơn tự động (ví dụ MealCandidateProviderPort) sẽ do Đức bổ sung khi
# triển khai planner/scorer/constraint_checker.
from __future__ import annotations

from abc import ABC, abstractmethod

from app.modules.meal_planning.domain import MealPlanEntity


class MealPlanRepositoryPort(ABC):
    @abstractmethod
    def create(self, plan: MealPlanEntity) -> MealPlanEntity: ...

    @abstractmethod
    def list_by_user(self, user_id: int) -> list[MealPlanEntity]: ...

    @abstractmethod
    def get(self, plan_id: int) -> MealPlanEntity | None: ...

    @abstractmethod
    def delete(self, plan_id: int) -> None: ...

# File: backend/app/modules/meal_planning/ports.py
#
# NOTE: port cho cả phần lưu trữ (MealPlanRepositoryPort) và phần sinh thực
# đơn tự động (MealCandidateProviderPort — Đức bổ sung cho planner/scorer/
# constraint_checker).
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

from app.modules.meal_planning.domain import (
    MealCandidate,
    MealPlanEntity,
    PlanRequest,
    ValidationResult,
)


class MealPlanRepositoryPort(ABC):
    @abstractmethod
    def create(self, plan: MealPlanEntity) -> MealPlanEntity: ...

    @abstractmethod
    def list_by_user(self, user_id: int) -> list[MealPlanEntity]: ...

    @abstractmethod
    def get(self, plan_id: int) -> MealPlanEntity | None: ...

    @abstractmethod
    def delete(self, plan_id: int) -> None: ...


class MealCandidateProviderPort(ABC):
    """Cung cấp danh sách món ăn hợp lệ (MealCandidate) cho planner.

    Việc loại trừ theo nguyên liệu (dị ứng + không ăn) được đẩy xuống tầng
    truy vấn để giảm số candidate phải xử lý; constraint_checker vẫn kiểm tra
    lại như một lớp an toàn (HC-02/HC-03)."""

    @abstractmethod
    def load_candidates(self, excluded_ingredient_ids: list[int]) -> list[MealCandidate]: ...


class MealPlannerPort(ABC):
    """Chiến lược sinh thực đơn (review D-19). Use case phụ thuộc vào port này
    chứ không vào HeuristicPlanner cụ thể, nên có thể thay chiến lược khác
    (ví dụ tối ưu tuyến tính) hoặc inject planner giả khi test."""

    @abstractmethod
    def generate(
        self,
        request: PlanRequest,
        candidates: list[MealCandidate],
        *,
        start_date: date | None = None,
    ) -> MealPlanEntity | ValidationResult: ...

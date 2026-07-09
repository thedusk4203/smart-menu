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

    @abstractmethod
    def load_candidates(self, excluded_ingredient_ids: list[int]) -> list[MealCandidate]: ...

    @abstractmethod
    def load_by_ids(self, meal_set_ids: list[int]) -> dict[int, MealCandidate]: ...


class MealPlannerPort(ABC):
    
    @abstractmethod
    def generate(
        self,
        request: PlanRequest,
        candidates: list[MealCandidate],
        *,
        start_date: date | None = None,
        seed: int | None = None,
    ) -> MealPlanEntity | ValidationResult: ...

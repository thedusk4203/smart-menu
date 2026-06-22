# File: backend/app/modules/meal_planning/domain.py
#
# NOTE (Bình -> nhóm): file này hiện chỉ chứa entity cho phần LƯU TRỮ
# thực đơn (API "lưu thực đơn" — deliverable của Bình). Phần sinh thực đơn
# tự động (candidate filtering, scoring, constraint checking — xem
# planner.py / scorer.py / constraint_checker.py) là trách nhiệm của Đức
# theo docs/architecture.md mục 6 và sẽ bổ sung domain object riêng
# (ví dụ PlanRequest, PlanCandidate...) khi anh triển khai phần đó.
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True)
class MealPlanEntity:
    id: int | None
    user_id: int
    name: str = "Thực đơn tuần"
    start_date: date = None
    end_date: date | None = None
    budget_limit: float | None = None
    total_cost: float = 0
    total_calories: float = 0
    plan_data: dict = field(default_factory=dict)

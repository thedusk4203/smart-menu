# File: backend/app/modules/profiles/domain.py
# Domain entities for user profiles. Pure Python — no FastAPI/SQLModel.
#
# NOTE (Bình -> nhóm): gender/activity_level/goal reuse app.shared.enums
# (đã được module nutrition của Đức dùng), để hai module luôn nói cùng một
# "ngôn ngữ" dữ liệu. Điểm cần chốt lại với Đức: FitnessGoal hiện chưa có
# giá trị "gain_weight" (tăng cân) dù SRS có yêu cầu mục tiêu này — em giữ
# nguyên enum của anh Đức ở đây, KHÔNG tự thêm, để tránh phá vỡ
# nutrition.calculator vốn đã test với 3 giá trị hiện có.
from __future__ import annotations

from dataclasses import dataclass

from app.shared.enums import ActivityLevel, FitnessGoal, Gender


@dataclass(frozen=True)
class UserProfileEntity:
    user_id: int
    full_name: str | None = None
    gender: Gender | None = None
    age: int | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    activity_level: ActivityLevel = ActivityLevel.SEDENTARY
    goal: FitnessGoal = FitnessGoal.MAINTAIN
    meals_per_day: int = 3
    daily_calorie_target: float | None = None
    daily_budget: float | None = None


@dataclass(frozen=True)
class ExcludedIngredientEntity:
    """Một nguyên liệu mà user dị ứng / không ăn — ràng buộc cứng cho
    meal_planning (constraint_checker phải loại các món chứa nguyên liệu này)."""
    id: int | None
    user_id: int
    ingredient_id: int
    reason: str  # "allergy" | "dislike" — xem app.shared.enums.ExclusionReason

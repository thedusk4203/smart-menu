from __future__ import annotations

from enum import Enum
from typing import Dict

class Gender(str, Enum):
    """Giới tính sinh học được sử dụng để tính BMR"""
    MALE = "male"
    FEMALE = "female"

# Activity Level

class ActivityLevel(str, Enum):
    """Mức độ hoạt động thể chất với hệ số TDEE tương ứng"""
    SEDENTARY = "sedentary"      # Little or no exercise
    LIGHT = "light"              # Light exercise 1-3 days/week
    MODERATE = "moderate"        # Moderate exercise 3-5 days/week
    ACTIVE = "active"            # Hard exercise 6-7 days/week

    @property
    def multiplier(self) -> float:
        return _ACTIVITY_MULTIPLIERS[self]


_ACTIVITY_MULTIPLIERS: Dict[ActivityLevel, float] = {
    ActivityLevel.SEDENTARY: 1.2,
    ActivityLevel.LIGHT: 1.375,
    ActivityLevel.MODERATE: 1.55,
    ActivityLevel.ACTIVE: 1.725,
}


# ---------------------------------------------------------------------------
# Fitness Goal
# ---------------------------------------------------------------------------

class FitnessGoal(str, Enum):
    """Mục tiêu tập luyện của người dùng với việc điều chỉnh lượng calo tương ứng."""
    MAINTAIN = "maintain"        # Keep current weight
    LOSE_WEIGHT = "lose_weight"  # Caloric deficit
    GAIN_MUSCLE = "gain_muscle"  # Caloric surplus
    GAIN_WEIGHT = "gain_weight"  # Caloric surplus (tăng cân, theo SRS)

    @property
    def calorie_adjustment(self) -> float:
        """Kcal added (positive) or subtracted (negative) from TDEE."""
        return _GOAL_ADJUSTMENTS[self]


_GOAL_ADJUSTMENTS: Dict[FitnessGoal, float] = {
    FitnessGoal.MAINTAIN: 0.0,
    FitnessGoal.LOSE_WEIGHT: -500.0,
    FitnessGoal.GAIN_MUSCLE: 300.0,
    FitnessGoal.GAIN_WEIGHT: 200.0,
}

class UserRole(str, Enum):
    """Vai trò tài khoản."""
    USER = "user"
    DATA_EDITOR = "data_editor"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class FoodGroup(str, Enum):
    """Nhóm thực phẩm của nguyên liệu."""
    PROTEIN = "protein"
    VEGETABLE = "vegetable"
    GRAIN = "grain"
    DAIRY = "dairy"
    FAT = "fat"
    FRUIT = "fruit"
    OTHER = "other"


class MealType(str, Enum):
    """Loại bữa ăn."""
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"


class CookingMethod(str, Enum):
    """Cách chế biến món ăn."""
    STIR_FRY = "stir_fry"
    BOIL = "boil"
    SOUP = "soup"
    BRAISE = "braise"
    STEAM = "steam"


class DishType(str, Enum):
    """Phân loại món thành phần mà planner dùng để ghép thành bữa."""
    STAPLE = "staple"
    SAVORY = "savory"
    SOUP = "soup"
    VEGETABLE_SIDE = "vegetable_side"
    SIDE = "side"
    BREAKFAST = "breakfast"

class ExclusionReason(str, Enum):
    """Lý do loại trừ nguyên liệu khỏi thực đơn của một người dùng."""
    ALLERGY = "allergy"
    DISLIKE = "dislike"

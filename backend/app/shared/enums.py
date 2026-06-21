# File: backend/app/shared/enums.py
# Shared enums used across multiple modules (nutrition, profiles, meal_planning).

from __future__ import annotations

from enum import Enum
from typing import Dict


# ---------------------------------------------------------------------------
# Gender
# ---------------------------------------------------------------------------

class Gender(str, Enum):
    """Biological sex used for BMR calculation."""
    MALE = "male"
    FEMALE = "female"


# ---------------------------------------------------------------------------
# Activity Level
# ---------------------------------------------------------------------------

class ActivityLevel(str, Enum):
    """Physical activity level with corresponding TDEE multiplier."""
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
    """User's fitness objective with corresponding calorie adjustment."""
    MAINTAIN = "maintain"        # Keep current weight
    LOSE_WEIGHT = "lose_weight"  # Caloric deficit
    GAIN_MUSCLE = "gain_muscle"  # Caloric surplus

    @property
    def calorie_adjustment(self) -> float:
        """Kcal added (positive) or subtracted (negative) from TDEE."""
        return _GOAL_ADJUSTMENTS[self]


_GOAL_ADJUSTMENTS: Dict[FitnessGoal, float] = {
    FitnessGoal.MAINTAIN: 0.0,
    FitnessGoal.LOSE_WEIGHT: -500.0,
    FitnessGoal.GAIN_MUSCLE: 300.0,
}


# ---------------------------------------------------------------------------
# Bổ sung bởi Bình (modules: identity, profiles, ingredients, meals)
# Các enum dưới đây KHÔNG đụng tới phần trên — chỉ thêm mới.
# ---------------------------------------------------------------------------

class UserRole(str, Enum):
    """Vai trò tài khoản."""
    USER = "user"
    ADMIN = "admin"


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


class ExclusionReason(str, Enum):
    """Lý do loại trừ nguyên liệu khỏi thực đơn của một người dùng."""
    ALLERGY = "allergy"
    DISLIKE = "dislike"

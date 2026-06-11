# File: backend/app/modules/nutrition/domain.py
# Domain objects for the nutrition module.
# Pure Python — no framework dependencies (no FastAPI, SQLModel, etc.).

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Sequence

# Import shared enums (used by profiles and other modules too)
from app.shared.enums import ActivityLevel, FitnessGoal, Gender  # noqa: F401


# ---------------------------------------------------------------------------
# Warning codes
# ---------------------------------------------------------------------------

class NutritionWarningCode(str, Enum):
    """Structured warning codes for extreme nutrition values.

    Using codes instead of free-text makes it easy for the frontend
    to localize, style, and programmatically handle warnings.
    """
    BMI_UNDERWEIGHT = "BMI_UNDERWEIGHT"
    BMI_OBESE = "BMI_OBESE"
    LOW_CALORIE_TARGET = "LOW_CALORIE_TARGET"
    HIGH_CALORIE_TARGET = "HIGH_CALORIE_TARGET"
    INFEASIBLE_CALORIE_TARGET = "INFEASIBLE_CALORIE_TARGET"


# ---------------------------------------------------------------------------
# Value Objects
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class MacroRatio:
    """Macronutrient percentage split. Values must sum to 100."""
    protein_pct: float
    fat_pct: float
    carb_pct: float

    def __post_init__(self) -> None:
        total = self.protein_pct + self.fat_pct + self.carb_pct
        if abs(total - 100.0) > 0.01:
            raise ValueError(
                f"Macro percentages must sum to 100, got {total:.2f} "
                f"(P={self.protein_pct}, F={self.fat_pct}, C={self.carb_pct})."
            )


# Preset macro ratios per fitness goal
MACRO_PRESETS: Dict[FitnessGoal, MacroRatio] = {
    FitnessGoal.MAINTAIN: MacroRatio(protein_pct=30, fat_pct=25, carb_pct=45),
    FitnessGoal.LOSE_WEIGHT: MacroRatio(protein_pct=40, fat_pct=25, carb_pct=35),
    FitnessGoal.GAIN_MUSCLE: MacroRatio(protein_pct=35, fat_pct=20, carb_pct=45),
}


@dataclass(frozen=True)
class NutritionWarning:
    """A single structured warning with code and human-readable message."""
    code: NutritionWarningCode
    message: str


@dataclass(frozen=True)
class NutritionTarget:
    """Calculated daily nutrition target for a user profile.

    Rounding rules:
    - bmr, tdee: 1 decimal place
    - target_calories: integer (round to whole number)
    - daily_protein_g, daily_fat_g, daily_carb_g: 1 decimal place
    - bmi: 1 decimal place

    Warnings use NutritionWarningCode for structured processing.
    warnings is a tuple for true immutability (list would allow .append()).

    is_feasible is False when target_calories falls below the safe minimum,
    in which case macros are zeroed out and planner should not proceed.
    """
    bmr: float
    tdee: float
    target_calories: int
    daily_protein_g: float
    daily_fat_g: float
    daily_carb_g: float
    bmi: float
    is_feasible: bool = True
    warnings: Sequence[NutritionWarning] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "warnings", tuple(self.warnings))

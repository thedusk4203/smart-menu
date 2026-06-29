from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Sequence

# Nhập các enum được chia sẻ (được sử dụng bởi các cấu hình và các module khác)
from app.shared.enums import ActivityLevel, FitnessGoal, Gender  # noqa: F401

# Warning codes

class NutritionWarningCode(str, Enum):

    BMI_UNDERWEIGHT = "BMI_UNDERWEIGHT"
    BMI_OBESE = "BMI_OBESE"
    LOW_CALORIE_TARGET = "LOW_CALORIE_TARGET"
    HIGH_CALORIE_TARGET = "HIGH_CALORIE_TARGET"
    INFEASIBLE_CALORIE_TARGET = "INFEASIBLE_CALORIE_TARGET"

# Value Objects

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
    FitnessGoal.GAIN_WEIGHT: MacroRatio(protein_pct=25, fat_pct=25, carb_pct=50),
}


@dataclass(frozen=True)
class NutritionWarning:
    code: NutritionWarningCode
    message: str


@dataclass(frozen=True)
class NutritionTarget:

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

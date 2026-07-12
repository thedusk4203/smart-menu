# Public API for the nutrition module.
#
# P1 fix: Only domain, calculator, and exceptions are eagerly imported.
# Schemas and use_cases require Pydantic and are imported lazily to keep
# the domain/calculator layer truly pure (no Pydantic dependency at import).
#
# Usage for pure domain:
#   from app.modules.nutrition import NutritionCalculator, NutritionTarget
#
# Usage for Pydantic DTOs:
#   from app.modules.nutrition.schemas import NutritionProfileInput
#   from app.modules.nutrition.use_cases import CalculateNutritionTargetUseCase

from app.modules.nutrition.calculator import NutritionCalculator
from app.modules.nutrition.domain import (
    MACRO_PRESETS,
    MacroRatio,
    NutritionTarget,
    NutritionWarning,
    NutritionWarningCode,
)
from app.modules.nutrition.exceptions import (
    InvalidEnumValueError,
    InvalidProfileDataError,
    NutritionCalculationError,
)

# Re-export shared enums for convenience
from app.shared.enums import ActivityLevel, FitnessGoal, Gender

__all__ = [
    # Shared Enums (re-exported)
    "Gender",
    "ActivityLevel",
    "FitnessGoal",
    # Domain
    "MacroRatio",
    "NutritionTarget",
    "NutritionWarning",
    "NutritionWarningCode",
    "MACRO_PRESETS",
    # Calculator
    "NutritionCalculator",
    # Exceptions
    "InvalidProfileDataError",
    "InvalidEnumValueError",
    "NutritionCalculationError",
]

# File: backend/app/modules/nutrition/exceptions.py
# Domain exceptions for the nutrition module.

from __future__ import annotations

from typing import Any, Sequence


class NutritionError(Exception):
    """Base exception for the nutrition module."""
    pass


class InvalidProfileDataError(NutritionError):
    """Raised when user profile data is outside valid ranges.

    Examples: age not in 15-100, weight not in 30-300 kg,
    height not in 100-250 cm.
    """

    def __init__(self, field: str, value: float, min_val: float, max_val: float) -> None:
        self.field = field
        self.value = value
        self.min_val = min_val
        self.max_val = max_val
        super().__init__(
            f"Invalid {field}: {value}. Must be between {min_val} and {max_val}."
        )


class InvalidEnumValueError(NutritionError):
    """Raised when an enum field receives an unrecognized value.

    Catches cases where DB or consumers pass a string/value that doesn't
    match any known enum member, preventing silent fallback to wrong logic.
    """

    def __init__(self, field: str, value: Any, allowed: Sequence[str]) -> None:
        self.field = field
        self.value = value
        self.allowed = list(allowed)
        allowed_str = ", ".join(f"'{v}'" for v in allowed)
        super().__init__(
            f"Invalid {field}: '{value}'. Must be one of: {allowed_str}."
        )


class NutritionCalculationError(NutritionError):
    """Raised when an unexpected error occurs during nutrition calculation.

    This is a safety-net exception that should rarely occur in practice.
    """

    def __init__(self, detail: str = "Unexpected error during nutrition calculation.") -> None:
        self.detail = detail
        super().__init__(detail)

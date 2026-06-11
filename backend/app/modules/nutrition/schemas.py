# File: backend/app/modules/nutrition/schemas.py
# Pydantic DTOs for nutrition module input/output.

from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field

from app.modules.nutrition.domain import NutritionWarningCode
from app.shared.enums import ActivityLevel, FitnessGoal, Gender


# ---------------------------------------------------------------------------
# Input
# ---------------------------------------------------------------------------

class NutritionProfileInput(BaseModel):
    """Input DTO for calculating a user's daily nutrition target.

    Values come from the user's profile (user_profiles table).
    """
    gender: Gender = Field(
        ...,
        description="Biological sex: 'male' or 'female'.",
    )
    age: int = Field(
        ...,
        ge=15,
        le=100,
        description="Age in years (15–100).",
    )
    weight_kg: float = Field(
        ...,
        ge=30.0,
        le=300.0,
        description="Body weight in kilograms (30–300).",
    )
    height_cm: float = Field(
        ...,
        ge=100.0,
        le=250.0,
        description="Height in centimeters (100–250).",
    )
    activity_level: ActivityLevel = Field(
        ...,
        description="Physical activity level: sedentary, light, moderate, or active.",
    )
    fitness_goal: FitnessGoal = Field(
        ...,
        description="Fitness objective: maintain, lose_weight, or gain_muscle.",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "gender": "male",
                    "age": 25,
                    "weight_kg": 70.0,
                    "height_cm": 175.0,
                    "activity_level": "moderate",
                    "fitness_goal": "maintain",
                }
            ]
        }
    }


# ---------------------------------------------------------------------------
# Warning DTO
# ---------------------------------------------------------------------------

class NutritionWarningResponse(BaseModel):
    """A single structured warning with code and human-readable message."""
    code: NutritionWarningCode = Field(
        ..., description="Machine-readable warning code."
    )
    message: str = Field(
        ..., description="Human-readable warning message in Vietnamese."
    )


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

class NutritionTargetResponse(BaseModel):
    """Output DTO representing the calculated daily nutrition target."""
    bmr: float = Field(
        ..., description="Basal Metabolic Rate (kcal), rounded to 1 decimal."
    )
    tdee: float = Field(
        ..., description="Total Daily Energy Expenditure (kcal), rounded to 1 decimal."
    )
    target_calories: int = Field(
        ..., description="Daily calorie target (kcal), rounded to integer."
    )
    daily_protein_g: float = Field(
        ..., description="Daily protein target (grams), rounded to 1 decimal."
    )
    daily_fat_g: float = Field(
        ..., description="Daily fat target (grams), rounded to 1 decimal."
    )
    daily_carb_g: float = Field(
        ..., description="Daily carbohydrate target (grams), rounded to 1 decimal."
    )
    bmi: float = Field(
        ..., description="Body Mass Index, rounded to 1 decimal."
    )
    is_feasible: bool = Field(
        default=True,
        description=(
            "False when target_calories is below the safe minimum (800 kcal). "
            "Planner should not proceed with an infeasible target."
        ),
    )
    warnings: List[NutritionWarningResponse] = Field(
        default_factory=list,
        description="Structured safety warnings with code and message.",
    )

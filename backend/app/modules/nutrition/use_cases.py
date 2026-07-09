# File: backend/app/modules/nutrition/use_cases.py
# Application-layer use cases for the nutrition module.

from __future__ import annotations

from app.modules.nutrition.calculator import NutritionCalculator
from app.modules.nutrition.schemas import (
    NutritionProfileInput,
    NutritionTargetResponse,
    NutritionWarningResponse,
)


class CalculateNutritionTargetUseCase:

    def __init__(self) -> None:
        self._calculator = NutritionCalculator()

    def execute(self, profile_input: NutritionProfileInput) -> NutritionTargetResponse:

        target = self._calculator.calculate_nutrition_target(
            gender=profile_input.gender,
            age=profile_input.age,
            weight_kg=profile_input.weight_kg,
            height_cm=profile_input.height_cm,
            activity_level=profile_input.activity_level,
            fitness_goal=profile_input.fitness_goal,
        )

        return NutritionTargetResponse(
            bmr=target.bmr,
            tdee=target.tdee,
            target_calories=target.target_calories,
            daily_protein_g=target.daily_protein_g,
            daily_fat_g=target.daily_fat_g,
            daily_carb_g=target.daily_carb_g,
            bmi=target.bmi,
            is_feasible=target.is_feasible,
            warnings=[
                NutritionWarningResponse(code=w.code, message=w.message)
                for w in target.warnings
            ],
        )

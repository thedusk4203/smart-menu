# File: backend/app/tests/test_nutrition/test_use_cases.py
# Unit tests for CalculateNutritionTargetUseCase.

import pytest

from app.modules.nutrition.domain import NutritionWarningCode
from app.modules.nutrition.schemas import (
    NutritionProfileInput,
    NutritionTargetResponse,
    NutritionWarningResponse,
)
from app.modules.nutrition.use_cases import CalculateNutritionTargetUseCase


@pytest.fixture
def use_case():
    return CalculateNutritionTargetUseCase()


class TestCalculateNutritionTargetUseCase:
    def test_returns_response_dto(self, use_case):
        profile = NutritionProfileInput(
            gender="male",
            age=25,
            weight_kg=70.0,
            height_cm=175.0,
            activity_level="moderate",
            fitness_goal="maintain",
        )
        result = use_case.execute(profile)
        assert isinstance(result, NutritionTargetResponse)

    def test_response_has_all_fields(self, use_case):
        profile = NutritionProfileInput(
            gender="female",
            age=28,
            weight_kg=58.0,
            height_cm=162.0,
            activity_level="light",
            fitness_goal="lose_weight",
        )
        result = use_case.execute(profile)

        assert result.target_calories > 0
        assert isinstance(result.target_calories, int)
        assert result.daily_protein_g > 0
        assert result.daily_fat_g > 0
        assert result.daily_carb_g > 0
        assert result.bmr > 0
        assert result.tdee > 0
        assert result.bmi > 0
        assert isinstance(result.is_feasible, bool)
        assert isinstance(result.warnings, list)

    def test_response_matches_calculator(self, use_case):
        """Use case output should match direct calculator output."""
        from app.modules.nutrition.calculator import NutritionCalculator
        from app.shared.enums import ActivityLevel, FitnessGoal, Gender

        profile = NutritionProfileInput(
            gender="male",
            age=30,
            weight_kg=80.0,
            height_cm=180.0,
            activity_level="active",
            fitness_goal="gain_muscle",
        )
        result = use_case.execute(profile)

        direct = NutritionCalculator.calculate_nutrition_target(
            gender=Gender.MALE,
            age=30,
            weight_kg=80.0,
            height_cm=180.0,
            activity_level=ActivityLevel.ACTIVE,
            fitness_goal=FitnessGoal.GAIN_MUSCLE,
        )

        assert result.target_calories == direct.target_calories
        assert result.daily_protein_g == direct.daily_protein_g
        assert result.daily_fat_g == direct.daily_fat_g
        assert result.daily_carb_g == direct.daily_carb_g
        assert result.bmr == direct.bmr
        assert result.tdee == direct.tdee
        assert result.bmi == direct.bmi
        assert result.is_feasible == direct.is_feasible
        assert len(result.warnings) == len(direct.warnings)

    def test_warnings_are_structured(self, use_case):
        """Warnings should have code and message."""
        profile = NutritionProfileInput(
            gender="female",
            age=50,
            weight_kg=45.0,
            height_cm=155.0,
            activity_level="sedentary",
            fitness_goal="lose_weight",
        )
        result = use_case.execute(profile)

        assert len(result.warnings) > 0
        for w in result.warnings:
            assert isinstance(w, NutritionWarningResponse)
            assert isinstance(w.code, NutritionWarningCode)
            assert len(w.message) > 0

    def test_infeasible_response(self, use_case):
        """P2a: Infeasible profile should return is_feasible=False, macros=0."""
        profile = NutritionProfileInput(
            gender="female",
            age=100,
            weight_kg=30.0,
            height_cm=100.0,
            activity_level="sedentary",
            fitness_goal="lose_weight",
        )
        result = use_case.execute(profile)

        assert result.is_feasible is False
        assert result.daily_protein_g == 0.0
        assert result.daily_fat_g == 0.0
        assert result.daily_carb_g == 0.0

        warning_codes = {w.code for w in result.warnings}
        assert NutritionWarningCode.INFEASIBLE_CALORIE_TARGET in warning_codes

    def test_serialization_to_dict(self, use_case):
        """Result should be serializable to JSON-compatible dict."""
        profile = NutritionProfileInput(
            gender="male",
            age=25,
            weight_kg=70.0,
            height_cm=175.0,
            activity_level="moderate",
            fitness_goal="maintain",
        )
        result = use_case.execute(profile)
        data = result.model_dump()

        assert isinstance(data, dict)
        assert "target_calories" in data
        assert "is_feasible" in data
        assert "warnings" in data
        assert isinstance(data["target_calories"], int)
        assert isinstance(data["is_feasible"], bool)

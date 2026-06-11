# File: backend/app/tests/test_nutrition/test_domain.py
# Unit tests for nutrition domain objects.

import pytest

from app.modules.nutrition.domain import (
    MACRO_PRESETS,
    MacroRatio,
    NutritionTarget,
    NutritionWarning,
    NutritionWarningCode,
)
from app.shared.enums import ActivityLevel, FitnessGoal, Gender


# ---------------------------------------------------------------------------
# Gender enum
# ---------------------------------------------------------------------------

class TestGender:
    def test_male_value(self):
        assert Gender.MALE == "male"

    def test_female_value(self):
        assert Gender.FEMALE == "female"

    def test_from_string(self):
        assert Gender("male") == Gender.MALE
        assert Gender("female") == Gender.FEMALE


# ---------------------------------------------------------------------------
# ActivityLevel enum
# ---------------------------------------------------------------------------

class TestActivityLevel:
    def test_sedentary_multiplier(self):
        assert ActivityLevel.SEDENTARY.multiplier == 1.2

    def test_light_multiplier(self):
        assert ActivityLevel.LIGHT.multiplier == 1.375

    def test_moderate_multiplier(self):
        assert ActivityLevel.MODERATE.multiplier == 1.55

    def test_active_multiplier(self):
        assert ActivityLevel.ACTIVE.multiplier == 1.725

    def test_from_string(self):
        assert ActivityLevel("sedentary") == ActivityLevel.SEDENTARY


# ---------------------------------------------------------------------------
# FitnessGoal enum
# ---------------------------------------------------------------------------

class TestFitnessGoal:
    def test_maintain_adjustment(self):
        assert FitnessGoal.MAINTAIN.calorie_adjustment == 0.0

    def test_lose_weight_adjustment(self):
        assert FitnessGoal.LOSE_WEIGHT.calorie_adjustment == -500.0

    def test_gain_muscle_adjustment(self):
        assert FitnessGoal.GAIN_MUSCLE.calorie_adjustment == 300.0


# ---------------------------------------------------------------------------
# NutritionWarningCode enum
# ---------------------------------------------------------------------------

class TestNutritionWarningCode:
    def test_all_codes(self):
        assert NutritionWarningCode.BMI_UNDERWEIGHT == "BMI_UNDERWEIGHT"
        assert NutritionWarningCode.BMI_OBESE == "BMI_OBESE"
        assert NutritionWarningCode.LOW_CALORIE_TARGET == "LOW_CALORIE_TARGET"
        assert NutritionWarningCode.HIGH_CALORIE_TARGET == "HIGH_CALORIE_TARGET"
        assert NutritionWarningCode.INFEASIBLE_CALORIE_TARGET == "INFEASIBLE_CALORIE_TARGET"

    def test_is_str_enum(self):
        assert isinstance(NutritionWarningCode.BMI_UNDERWEIGHT, str)


# ---------------------------------------------------------------------------
# MacroRatio value object
# ---------------------------------------------------------------------------

class TestMacroRatio:
    def test_valid_ratio(self):
        ratio = MacroRatio(protein_pct=30, fat_pct=25, carb_pct=45)
        assert ratio.protein_pct == 30
        assert ratio.fat_pct == 25
        assert ratio.carb_pct == 45

    def test_invalid_ratio_raises(self):
        with pytest.raises(ValueError, match="must sum to 100"):
            MacroRatio(protein_pct=30, fat_pct=30, carb_pct=30)

    def test_frozen(self):
        ratio = MacroRatio(protein_pct=30, fat_pct=25, carb_pct=45)
        with pytest.raises(AttributeError):
            ratio.protein_pct = 50  # type: ignore[misc]


# ---------------------------------------------------------------------------
# MACRO_PRESETS
# ---------------------------------------------------------------------------

class TestMacroPresets:
    def test_all_goals_have_presets(self):
        for goal in FitnessGoal:
            assert goal in MACRO_PRESETS

    def test_presets_sum_to_100(self):
        for goal, ratio in MACRO_PRESETS.items():
            total = ratio.protein_pct + ratio.fat_pct + ratio.carb_pct
            assert abs(total - 100.0) < 0.01, f"{goal}: {total}"

    def test_maintain_preset(self):
        r = MACRO_PRESETS[FitnessGoal.MAINTAIN]
        assert r.protein_pct == 30
        assert r.fat_pct == 25
        assert r.carb_pct == 45

    def test_lose_weight_preset(self):
        r = MACRO_PRESETS[FitnessGoal.LOSE_WEIGHT]
        assert r.protein_pct == 40
        assert r.fat_pct == 25
        assert r.carb_pct == 35

    def test_gain_muscle_preset(self):
        r = MACRO_PRESETS[FitnessGoal.GAIN_MUSCLE]
        assert r.protein_pct == 35
        assert r.fat_pct == 20
        assert r.carb_pct == 45


# ---------------------------------------------------------------------------
# NutritionWarning value object
# ---------------------------------------------------------------------------

class TestNutritionWarning:
    def test_creation(self):
        w = NutritionWarning(
            code=NutritionWarningCode.BMI_UNDERWEIGHT,
            message="BMI too low",
        )
        assert w.code == NutritionWarningCode.BMI_UNDERWEIGHT
        assert w.message == "BMI too low"

    def test_frozen(self):
        w = NutritionWarning(
            code=NutritionWarningCode.BMI_OBESE,
            message="BMI too high",
        )
        with pytest.raises(AttributeError):
            w.code = NutritionWarningCode.BMI_UNDERWEIGHT  # type: ignore[misc]


# ---------------------------------------------------------------------------
# NutritionTarget value object
# ---------------------------------------------------------------------------

class TestNutritionTarget:
    def test_creation(self):
        target = NutritionTarget(
            bmr=1700.0,
            tdee=2000.0,
            target_calories=2000,
            daily_protein_g=150.0,
            daily_fat_g=55.6,
            daily_carb_g=225.0,
            bmi=22.5,
            is_feasible=True,
            warnings=(),
        )
        assert target.target_calories == 2000
        assert isinstance(target.target_calories, int)
        assert target.is_feasible is True
        assert target.warnings == ()

    def test_with_warnings(self):
        target = NutritionTarget(
            bmr=1500.0,
            tdee=1600.0,
            target_calories=1100,
            daily_protein_g=100.0,
            daily_fat_g=30.0,
            daily_carb_g=100.0,
            bmi=17.0,
            warnings=(
                NutritionWarning(
                    code=NutritionWarningCode.BMI_UNDERWEIGHT,
                    message="Low BMI",
                ),
                NutritionWarning(
                    code=NutritionWarningCode.LOW_CALORIE_TARGET,
                    message="Low calories",
                ),
            ),
        )
        assert len(target.warnings) == 2
        assert target.warnings[0].code == NutritionWarningCode.BMI_UNDERWEIGHT
        assert target.warnings[1].code == NutritionWarningCode.LOW_CALORIE_TARGET

    def test_infeasible(self):
        target = NutritionTarget(
            bmr=1000.0,
            tdee=1200.0,
            target_calories=700,
            daily_protein_g=0.0,
            daily_fat_g=0.0,
            daily_carb_g=0.0,
            bmi=18.7,
            is_feasible=False,
            warnings=(
                NutritionWarning(
                    code=NutritionWarningCode.INFEASIBLE_CALORIE_TARGET,
                    message="Too low",
                ),
            ),
        )
        assert target.is_feasible is False
        assert target.daily_protein_g == 0.0
        assert target.daily_fat_g == 0.0
        assert target.daily_carb_g == 0.0

    def test_frozen_field(self):
        target = NutritionTarget(
            bmr=1700.0,
            tdee=2000.0,
            target_calories=2000,
            daily_protein_g=150.0,
            daily_fat_g=55.6,
            daily_carb_g=225.0,
            bmi=22.5,
        )
        with pytest.raises(AttributeError):
            target.target_calories = 3000  # type: ignore[misc]

    def test_warnings_tuple_immutable(self):
        """P2b: warnings is a tuple, so .append() is not possible."""
        target = NutritionTarget(
            bmr=1700.0,
            tdee=2000.0,
            target_calories=2000,
            daily_protein_g=150.0,
            daily_fat_g=55.6,
            daily_carb_g=225.0,
            bmi=22.5,
            warnings=(),
        )
        assert isinstance(target.warnings, tuple)
        with pytest.raises(AttributeError):
            target.warnings.append(  # type: ignore[attr-defined]
                NutritionWarning(
                    code=NutritionWarningCode.BMI_OBESE,
                    message="test",
                )
            )

    def test_warnings_list_input_converted_to_tuple(self):
        """P2: callers may pass a list, but the value object stores a tuple."""
        warning = NutritionWarning(
            code=NutritionWarningCode.LOW_CALORIE_TARGET,
            message="test",
        )
        target = NutritionTarget(
            bmr=1700.0,
            tdee=2000.0,
            target_calories=700,
            daily_protein_g=0.0,
            daily_fat_g=0.0,
            daily_carb_g=0.0,
            bmi=22.5,
            is_feasible=False,
            warnings=[warning],
        )

        assert target.warnings == (warning,)
        assert isinstance(target.warnings, tuple)
        with pytest.raises(AttributeError):
            target.warnings.append(warning)  # type: ignore[attr-defined]

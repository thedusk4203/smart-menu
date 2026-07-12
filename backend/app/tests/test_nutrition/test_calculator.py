# Unit tests for NutritionCalculator.

import pytest

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
)
from app.shared.enums import ActivityLevel, FitnessGoal, Gender


# ---------------------------------------------------------------------------
# BMI
# ---------------------------------------------------------------------------

class TestCalculateBMI:
    def test_normal_bmi(self):
        # 70 / (1.75^2) = 70 / 3.0625 = 22.857... → 22.9
        bmi = NutritionCalculator.calculate_bmi(70.0, 175.0)
        assert bmi == 22.9

    def test_underweight_bmi(self):
        bmi = NutritionCalculator.calculate_bmi(45.0, 170.0)
        assert bmi < 18.5

    def test_obese_bmi(self):
        bmi = NutritionCalculator.calculate_bmi(110.0, 170.0)
        assert bmi > 30.0

    def test_rounding_1_decimal(self):
        bmi = NutritionCalculator.calculate_bmi(70.0, 175.0)
        assert bmi == round(bmi, 1)


# ---------------------------------------------------------------------------
# BMR (Mifflin-St Jeor)
# ---------------------------------------------------------------------------

class TestCalculateBMR:
    def test_male_bmr(self):
        # Male: 10*70 + 6.25*175 - 5*25 + 5 = 1673.75 → 1673.8
        bmr = NutritionCalculator.calculate_bmr(Gender.MALE, 70.0, 175.0, 25)
        assert bmr == 1673.8

    def test_female_bmr(self):
        # Female: 10*60 + 6.25*165 - 5*30 - 161 = 1320.25 → 1320.2
        bmr = NutritionCalculator.calculate_bmr(Gender.FEMALE, 60.0, 165.0, 30)
        assert bmr == 1320.2

    def test_male_higher_than_female_same_stats(self):
        male_bmr = NutritionCalculator.calculate_bmr(Gender.MALE, 70.0, 170.0, 30)
        female_bmr = NutritionCalculator.calculate_bmr(Gender.FEMALE, 70.0, 170.0, 30)
        assert male_bmr > female_bmr

    def test_older_person_lower_bmr(self):
        young_bmr = NutritionCalculator.calculate_bmr(Gender.MALE, 70.0, 175.0, 25)
        old_bmr = NutritionCalculator.calculate_bmr(Gender.MALE, 70.0, 175.0, 55)
        assert young_bmr > old_bmr

    def test_rounding_1_decimal(self):
        bmr = NutritionCalculator.calculate_bmr(Gender.MALE, 70.0, 175.0, 25)
        assert bmr == round(bmr, 1)

    def test_invalid_gender_raises(self):
        """P3: Unrecognized gender should raise InvalidEnumValueError."""
        with pytest.raises(InvalidEnumValueError, match="gender"):
            NutritionCalculator.calculate_bmr("other", 70.0, 175.0, 25)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# TDEE
# ---------------------------------------------------------------------------

class TestCalculateTDEE:
    def test_sedentary(self):
        bmr = 1673.8
        tdee = NutritionCalculator.calculate_tdee(bmr, ActivityLevel.SEDENTARY)
        assert tdee == round(1673.8 * 1.2, 1)

    def test_active(self):
        bmr = 1673.8
        tdee = NutritionCalculator.calculate_tdee(bmr, ActivityLevel.ACTIVE)
        assert tdee == round(1673.8 * 1.725, 1)

    def test_higher_activity_higher_tdee(self):
        bmr = 1500.0
        sedentary = NutritionCalculator.calculate_tdee(bmr, ActivityLevel.SEDENTARY)
        active = NutritionCalculator.calculate_tdee(bmr, ActivityLevel.ACTIVE)
        assert active > sedentary

    def test_rounding_1_decimal(self):
        tdee = NutritionCalculator.calculate_tdee(1673.8, ActivityLevel.MODERATE)
        assert tdee == round(tdee, 1)


# ---------------------------------------------------------------------------
# Calorie adjustment
# ---------------------------------------------------------------------------

class TestAdjustCalories:
    def test_maintain(self):
        result = NutritionCalculator.adjust_calories(2000.0, FitnessGoal.MAINTAIN)
        assert result == 2000
        assert isinstance(result, int)

    def test_lose_weight(self):
        result = NutritionCalculator.adjust_calories(2000.0, FitnessGoal.LOSE_WEIGHT)
        assert result == 1500
        assert isinstance(result, int)

    def test_gain_muscle(self):
        result = NutritionCalculator.adjust_calories(2000.0, FitnessGoal.GAIN_MUSCLE)
        assert result == 2300
        assert isinstance(result, int)

    def test_gain_weight(self):
        result = NutritionCalculator.adjust_calories(2000.0, FitnessGoal.GAIN_WEIGHT)
        assert result == 2200
        assert isinstance(result, int)

    def test_never_negative(self):
        result = NutritionCalculator.adjust_calories(300.0, FitnessGoal.LOSE_WEIGHT)
        assert result >= 0

    def test_rounds_to_integer(self):
        result = NutritionCalculator.adjust_calories(2000.7, FitnessGoal.MAINTAIN)
        assert isinstance(result, int)
        assert result == 2001


# ---------------------------------------------------------------------------
# Macro calculation
# ---------------------------------------------------------------------------

class TestCalculateMacros:
    def test_maintain_macros(self):
        ratio = MACRO_PRESETS[FitnessGoal.MAINTAIN]
        protein, fat, carb = NutritionCalculator.calculate_macros(2000, ratio)
        assert protein == 150.0
        assert fat == 55.6
        assert carb == 225.0

    def test_lose_weight_macros(self):
        ratio = MACRO_PRESETS[FitnessGoal.LOSE_WEIGHT]
        protein, fat, carb = NutritionCalculator.calculate_macros(1500, ratio)
        assert protein == 150.0
        assert fat == 41.7
        assert carb == 131.2

    def test_gain_muscle_macros(self):
        ratio = MACRO_PRESETS[FitnessGoal.GAIN_MUSCLE]
        protein, fat, carb = NutritionCalculator.calculate_macros(2300, ratio)
        assert protein == 201.2
        assert fat == 51.1
        assert carb == 258.8

    def test_gain_weight_macros(self):
        ratio = MACRO_PRESETS[FitnessGoal.GAIN_WEIGHT]
        protein, fat, carb = NutritionCalculator.calculate_macros(2200, ratio)
        assert protein == 137.5
        assert fat == 61.1
        assert carb == 275.0

    def test_rounding_1_decimal(self):
        ratio = MACRO_PRESETS[FitnessGoal.MAINTAIN]
        protein, fat, carb = NutritionCalculator.calculate_macros(2000, ratio)
        assert protein == round(protein, 1)
        assert fat == round(fat, 1)
        assert carb == round(carb, 1)


# ---------------------------------------------------------------------------
# Safety warnings
# ---------------------------------------------------------------------------

class TestCheckWarnings:
    def test_no_warnings_normal(self):
        warnings = NutritionCalculator.check_warnings(
            bmi=22.9, tdee=2008.6, target_calories=2009
        )
        assert warnings == []

    def test_underweight_warning(self):
        warnings = NutritionCalculator.check_warnings(
            bmi=17.0, tdee=1800.0, target_calories=1800
        )
        assert len(warnings) == 1
        assert warnings[0].code == NutritionWarningCode.BMI_UNDERWEIGHT

    def test_obese_warning(self):
        warnings = NutritionCalculator.check_warnings(
            bmi=32.0, tdee=2500.0, target_calories=2500
        )
        assert len(warnings) == 1
        assert warnings[0].code == NutritionWarningCode.BMI_OBESE

    def test_low_calories_warning(self):
        warnings = NutritionCalculator.check_warnings(
            bmi=22.0, tdee=1500.0, target_calories=1100
        )
        assert len(warnings) == 1
        assert warnings[0].code == NutritionWarningCode.LOW_CALORIE_TARGET

    def test_high_calories_warning(self):
        warnings = NutritionCalculator.check_warnings(
            bmi=22.0, tdee=4200.0, target_calories=4200
        )
        assert len(warnings) == 1
        assert warnings[0].code == NutritionWarningCode.HIGH_CALORIE_TARGET

    def test_multiple_warnings(self):
        warnings = NutritionCalculator.check_warnings(
            bmi=16.0, tdee=1300.0, target_calories=1100
        )
        assert len(warnings) == 2
        codes = {w.code for w in warnings}
        assert NutritionWarningCode.BMI_UNDERWEIGHT in codes
        assert NutritionWarningCode.LOW_CALORIE_TARGET in codes

    def test_warning_has_message(self):
        warnings = NutritionCalculator.check_warnings(
            bmi=17.0, tdee=1800.0, target_calories=1800
        )
        assert warnings[0].message
        assert len(warnings[0].message) > 0


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------

class TestValidateInputs:
    def test_valid_inputs(self):
        NutritionCalculator.validate_inputs(age=25, weight_kg=70.0, height_cm=175.0)

    def test_age_too_low(self):
        with pytest.raises(InvalidProfileDataError, match="age"):
            NutritionCalculator.validate_inputs(age=10, weight_kg=70.0, height_cm=175.0)

    def test_age_too_high(self):
        with pytest.raises(InvalidProfileDataError, match="age"):
            NutritionCalculator.validate_inputs(age=101, weight_kg=70.0, height_cm=175.0)

    def test_weight_too_low(self):
        with pytest.raises(InvalidProfileDataError, match="weight"):
            NutritionCalculator.validate_inputs(age=25, weight_kg=20.0, height_cm=175.0)

    def test_weight_too_high(self):
        with pytest.raises(InvalidProfileDataError, match="weight"):
            NutritionCalculator.validate_inputs(age=25, weight_kg=350.0, height_cm=175.0)

    def test_height_too_low(self):
        with pytest.raises(InvalidProfileDataError, match="height"):
            NutritionCalculator.validate_inputs(age=25, weight_kg=70.0, height_cm=80.0)

    def test_height_too_high(self):
        with pytest.raises(InvalidProfileDataError, match="height"):
            NutritionCalculator.validate_inputs(age=25, weight_kg=70.0, height_cm=260.0)

    def test_boundary_min_age(self):
        NutritionCalculator.validate_inputs(age=15, weight_kg=70.0, height_cm=175.0)

    def test_boundary_max_age(self):
        NutritionCalculator.validate_inputs(age=100, weight_kg=70.0, height_cm=175.0)


# ---------------------------------------------------------------------------
# End-to-end: calculate_nutrition_target
# ---------------------------------------------------------------------------

class TestCalculateNutritionTarget:
    def test_male_maintain_moderate(self):
        """Standard male, maintain weight, moderate activity."""
        target = NutritionCalculator.calculate_nutrition_target(
            gender=Gender.MALE,
            age=25,
            weight_kg=70.0,
            height_cm=175.0,
            activity_level=ActivityLevel.MODERATE,
            fitness_goal=FitnessGoal.MAINTAIN,
        )

        assert isinstance(target, NutritionTarget)
        assert target.bmr == 1673.8
        assert target.tdee == 2594.4
        assert target.target_calories == 2594
        assert isinstance(target.target_calories, int)
        assert target.bmi == 22.9
        assert target.is_feasible is True
        assert target.warnings == ()

        # Macros from target_calories
        cal = target.target_calories
        assert target.daily_protein_g == round(cal * 30 / 100 / 4, 1)
        assert target.daily_fat_g == round(cal * 25 / 100 / 9, 1)
        assert target.daily_carb_g == round(cal * 45 / 100 / 4, 1)

    def test_female_lose_weight_light(self):
        """Standard female, lose weight, light activity."""
        target = NutritionCalculator.calculate_nutrition_target(
            gender=Gender.FEMALE,
            age=30,
            weight_kg=60.0,
            height_cm=165.0,
            activity_level=ActivityLevel.LIGHT,
            fitness_goal=FitnessGoal.LOSE_WEIGHT,
        )
        assert target.bmr == 1320.2
        assert target.tdee == 1815.3
        assert target.target_calories == 1315
        assert isinstance(target.target_calories, int)
        assert target.is_feasible is True
        assert target.warnings == ()

    def test_gain_muscle(self):
        """Male, gain muscle, active."""
        target = NutritionCalculator.calculate_nutrition_target(
            gender=Gender.MALE,
            age=22,
            weight_kg=80.0,
            height_cm=180.0,
            activity_level=ActivityLevel.ACTIVE,
            fitness_goal=FitnessGoal.GAIN_MUSCLE,
        )
        expected = round(target.tdee + 300)
        assert target.target_calories == expected
        assert target.is_feasible is True

        expected_protein = round(target.target_calories * 0.35 / 4, 1)
        assert target.daily_protein_g == expected_protein

    def test_infeasible_extreme_profile(self):
        """P2a: female, 100y, 30kg, 100cm, sedentary, lose_weight → infeasible."""
        target = NutritionCalculator.calculate_nutrition_target(
            gender=Gender.FEMALE,
            age=100,
            weight_kg=30.0,
            height_cm=100.0,
            activity_level=ActivityLevel.SEDENTARY,
            fitness_goal=FitnessGoal.LOSE_WEIGHT,
        )
        assert target.is_feasible is False
        assert target.target_calories < 800
        assert target.daily_protein_g == 0.0
        assert target.daily_fat_g == 0.0
        assert target.daily_carb_g == 0.0

        warning_codes = {w.code for w in target.warnings}
        assert NutritionWarningCode.INFEASIBLE_CALORIE_TARGET in warning_codes

    def test_infeasible_light_person_lose_weight(self):
        """P3: Infeasible keeps the actual unsafe calorie target for explanation."""
        target = NutritionCalculator.calculate_nutrition_target(
            gender=Gender.FEMALE,
            age=50,
            weight_kg=45.0,
            height_cm=155.0,
            activity_level=ActivityLevel.SEDENTARY,
            fitness_goal=FitnessGoal.LOSE_WEIGHT,
        )
        # BMR ~1007.8, TDEE ~1209.4, target ~709 → infeasible (< 800)
        assert target.is_feasible is False
        assert target.target_calories > 0
        assert target.target_calories < 800
        assert target.daily_protein_g == 0.0
        assert target.daily_fat_g == 0.0
        assert target.daily_carb_g == 0.0

        warning_codes = {w.code for w in target.warnings}
        assert NutritionWarningCode.INFEASIBLE_CALORIE_TARGET in warning_codes
        # Should also have LOW_CALORIE_TARGET from check_warnings
        assert NutritionWarningCode.LOW_CALORIE_TARGET in warning_codes

    def test_invalid_age_raises(self):
        with pytest.raises(InvalidProfileDataError):
            NutritionCalculator.calculate_nutrition_target(
                gender=Gender.MALE,
                age=5,
                weight_kg=70.0,
                height_cm=175.0,
                activity_level=ActivityLevel.MODERATE,
                fitness_goal=FitnessGoal.MAINTAIN,
            )

    def test_invalid_gender_raises(self):
        """P3: Invalid gender in orchestrator should raise."""
        with pytest.raises(InvalidEnumValueError):
            NutritionCalculator.calculate_nutrition_target(
                gender="non_binary",  # type: ignore[arg-type]
                age=25,
                weight_kg=70.0,
                height_cm=175.0,
                activity_level=ActivityLevel.MODERATE,
                fitness_goal=FitnessGoal.MAINTAIN,
            )

    def test_all_values_correctly_typed(self):
        """Verify rounding rules and types."""
        target = NutritionCalculator.calculate_nutrition_target(
            gender=Gender.MALE,
            age=25,
            weight_kg=70.0,
            height_cm=175.0,
            activity_level=ActivityLevel.MODERATE,
            fitness_goal=FitnessGoal.MAINTAIN,
        )
        assert isinstance(target.bmr, float)
        assert isinstance(target.tdee, float)
        assert isinstance(target.target_calories, int)
        assert isinstance(target.daily_protein_g, float)
        assert isinstance(target.daily_fat_g, float)
        assert isinstance(target.daily_carb_g, float)
        assert isinstance(target.bmi, float)
        assert isinstance(target.is_feasible, bool)
        assert isinstance(target.warnings, tuple)

    def test_warnings_are_tuple(self):
        """P2b: Warnings should be a tuple, not a list."""
        target = NutritionCalculator.calculate_nutrition_target(
            gender=Gender.MALE,
            age=25,
            weight_kg=70.0,
            height_cm=175.0,
            activity_level=ActivityLevel.MODERATE,
            fitness_goal=FitnessGoal.MAINTAIN,
        )
        assert isinstance(target.warnings, tuple)

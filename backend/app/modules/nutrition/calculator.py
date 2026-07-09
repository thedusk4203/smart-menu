from __future__ import annotations

from typing import List, Tuple

from app.modules.nutrition.constants import (
    AGE_MAX,
    AGE_MIN,
    BMI_OBESE,
    BMI_UNDERWEIGHT,
    CALORIES_TOO_HIGH,
    CALORIES_TOO_LOW,
    HEIGHT_MAX_CM,
    HEIGHT_MIN_CM,
    KCAL_PER_G_CARB,
    KCAL_PER_G_FAT,
    KCAL_PER_G_PROTEIN,
    MINIMUM_SAFE_CALORIES,
    WEIGHT_MAX_KG,
    WEIGHT_MIN_KG,
    MifflinStJeor,
)
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
from app.shared.enums import ActivityLevel, FitnessGoal, Gender


class NutritionCalculator:
    """Stateless calculator for BMR, TDEE, macro targets, and safety warnings.

    All public methods are static — the class is used purely for namespace grouping.
    """

    @staticmethod
    def validate_inputs(
        age: int,
        weight_kg: float,
        height_cm: float,
    ) -> None:
        if not (AGE_MIN <= age <= AGE_MAX):
            raise InvalidProfileDataError("age", age, AGE_MIN, AGE_MAX)
        if not (WEIGHT_MIN_KG <= weight_kg <= WEIGHT_MAX_KG):
            raise InvalidProfileDataError("weight_kg", weight_kg, WEIGHT_MIN_KG, WEIGHT_MAX_KG)
        if not (HEIGHT_MIN_CM <= height_cm <= HEIGHT_MAX_CM):
            raise InvalidProfileDataError("height_cm", height_cm, HEIGHT_MIN_CM, HEIGHT_MAX_CM)

    # Core calculations
    @staticmethod
    def calculate_bmi(weight_kg: float, height_cm: float) -> float:
        """Calculate Body Mass Index.

        Formula: weight_kg / (height_m ** 2)
        Returns: BMI rounded to 1 decimal place.
        """
        height_m = height_cm / 100.0
        return round(weight_kg / (height_m ** 2), 1)

    @staticmethod
    def calculate_bmr(
        gender: Gender,
        weight_kg: float,
        height_cm: float,
        age: int,
    ) -> float:
        """Calculate Basal Metabolic Rate using Mifflin-St Jeor equation.

        Male:   10 × weight + 6.25 × height − 5 × age + 5
        Female: 10 × weight + 6.25 × height − 5 × age − 161

        Returns: BMR rounded to 1 decimal place.

        Raises:
            InvalidEnumValueError: If gender is not a recognized Gender value.
        """
        base = (
            MifflinStJeor.WEIGHT_COEFF * weight_kg
            + MifflinStJeor.HEIGHT_COEFF * height_cm
            - MifflinStJeor.AGE_COEFF * age
        )
        if gender == Gender.MALE:
            return round(base + MifflinStJeor.MALE_OFFSET, 1)
        elif gender == Gender.FEMALE:
            return round(base + MifflinStJeor.FEMALE_OFFSET, 1)
        else:
            raise InvalidEnumValueError(
                "gender", gender, [g.value for g in Gender]
            )

    @staticmethod
    def calculate_tdee(bmr: float, activity_level: ActivityLevel) -> float:
        """Calculate Total Daily Energy Expenditure.

        Formula: BMR × activity multiplier.
        Returns: TDEE rounded to 1 decimal place.
        """
        return round(bmr * activity_level.multiplier, 1)

    @staticmethod
    def adjust_calories(tdee: float, fitness_goal: FitnessGoal) -> int:
        """Adjust TDEE based on fitness goal.

        - maintain:     TDEE + 0
        - lose_weight:  TDEE − 500
        - gain_muscle:  TDEE + 300

        Returns: target_calories rounded to integer. Never goes below 0.
        """
        adjusted = tdee + fitness_goal.calorie_adjustment
        return round(max(adjusted, 0))

    @staticmethod
    def calculate_macros(
        target_calories: int,
        macro_ratio: MacroRatio,
    ) -> Tuple[float, float, float]:
        """Convert calorie target + macro ratio into grams.

        - Protein: 4 kcal/g
        - Fat:     9 kcal/g
        - Carb:    4 kcal/g

        Returns: (protein_g, fat_g, carb_g) each rounded to 1 decimal place.
        """
        protein_g = round((target_calories * macro_ratio.protein_pct / 100) / KCAL_PER_G_PROTEIN, 1)
        fat_g = round((target_calories * macro_ratio.fat_pct / 100) / KCAL_PER_G_FAT, 1)
        carb_g = round((target_calories * macro_ratio.carb_pct / 100) / KCAL_PER_G_CARB, 1)
        return protein_g, fat_g, carb_g

    # ------------------------------------------------------------------
    # Safety warnings
    # ------------------------------------------------------------------

    @staticmethod
    def check_warnings(
        bmi: float,
        tdee: float,
        target_calories: int,
    ) -> List[NutritionWarning]:

        warnings: List[NutritionWarning] = []

        if bmi < BMI_UNDERWEIGHT:
            warnings.append(NutritionWarning(
                code=NutritionWarningCode.BMI_UNDERWEIGHT,
                message=(
                    f"BMI của bạn ({bmi}) thấp hơn mức khỏe mạnh (< {BMI_UNDERWEIGHT}). "
                    "Nên tham khảo ý kiến chuyên gia dinh dưỡng."
                ),
            ))
        if bmi > BMI_OBESE:
            warnings.append(NutritionWarning(
                code=NutritionWarningCode.BMI_OBESE,
                message=(
                    f"BMI của bạn ({bmi}) thuộc mức béo phì (> {BMI_OBESE}). "
                    "Nên tham khảo ý kiến bác sĩ trước khi thay đổi chế độ ăn đáng kể."
                ),
            ))
        if target_calories < CALORIES_TOO_LOW:
            warnings.append(NutritionWarning(
                code=NutritionWarningCode.LOW_CALORIE_TARGET,
                message=(
                    f"Mục tiêu calo ({target_calories} kcal/ngày) thấp hơn mức an toàn tối thiểu "
                    f"({CALORIES_TOO_LOW} kcal). Hệ thống khuyến nghị không ăn dưới mức này."
                ),
            ))
        if target_calories > CALORIES_TOO_HIGH:
            warnings.append(NutritionWarning(
                code=NutritionWarningCode.HIGH_CALORIE_TARGET,
                message=(
                    f"Mục tiêu calo ({target_calories} kcal/ngày) cao bất thường "
                    f"(> {CALORIES_TOO_HIGH} kcal). Hãy kiểm tra lại thông tin hồ sơ."
                ),
            ))

        return warnings

    # Orchestrator

    @staticmethod
    def calculate_nutrition_target(
        gender: Gender,
        age: int,
        weight_kg: float,
        height_cm: float,
        activity_level: ActivityLevel,
        fitness_goal: FitnessGoal,
    ) -> NutritionTarget:

        try:
            NutritionCalculator.validate_inputs(age, weight_kg, height_cm)

            bmi = NutritionCalculator.calculate_bmi(weight_kg, height_cm)
            bmr = NutritionCalculator.calculate_bmr(gender, weight_kg, height_cm, age)
            tdee = NutritionCalculator.calculate_tdee(bmr, activity_level)
            target_calories = NutritionCalculator.adjust_calories(tdee, fitness_goal)

            # --- Feasibility check ---
            if target_calories < MINIMUM_SAFE_CALORIES:
                # Infeasible: skip macro calculation, zero everything out
                warnings = NutritionCalculator.check_warnings(bmi, tdee, target_calories)
                warnings.append(NutritionWarning(
                    code=NutritionWarningCode.INFEASIBLE_CALORIE_TARGET,
                    message=(
                        f"Mục tiêu calo ({target_calories} kcal/ngày) quá thấp để lập "
                        f"thực đơn an toàn (< {MINIMUM_SAFE_CALORIES} kcal). "
                        "Hãy tăng ngân sách, giảm mức giảm cân, hoặc tăng mức vận động."
                    ),
                ))
                return NutritionTarget(
                    bmr=bmr,
                    tdee=tdee,
                    target_calories=target_calories,
                    daily_protein_g=0.0,
                    daily_fat_g=0.0,
                    daily_carb_g=0.0,
                    bmi=bmi,
                    is_feasible=False,
                    warnings=tuple(warnings),
                )

            # --- Feasible path ---
            macro_ratio = MACRO_PRESETS[fitness_goal]
            protein_g, fat_g, carb_g = NutritionCalculator.calculate_macros(
                target_calories, macro_ratio
            )

            warnings = NutritionCalculator.check_warnings(bmi, tdee, target_calories)

            return NutritionTarget(
                bmr=bmr,
                tdee=tdee,
                target_calories=target_calories,
                daily_protein_g=protein_g,
                daily_fat_g=fat_g,
                daily_carb_g=carb_g,
                bmi=bmi,
                is_feasible=True,
                warnings=tuple(warnings),
            )
        except (InvalidProfileDataError, InvalidEnumValueError, ValueError):
            raise
        except Exception as exc:
            raise NutritionCalculationError(
                f"Unexpected error calculating nutrition target: {exc}"
            ) from exc

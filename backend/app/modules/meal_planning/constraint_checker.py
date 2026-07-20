"""Independent hard-constraint validation for composed dish meals."""
from __future__ import annotations

from app.modules.meal_planning.composition import slots_for, valid_meal_types
from app.modules.meal_planning.domain import ComposedMeal, DishCandidate, PlanRequest, ValidationResult
from app.shared.enums import DishType


def has_valid_data(candidate: DishCandidate) -> bool:
    """Planner-ready means complete recipe/nutrition and non-negative usage value.

    Pantry/ignored ingredients can make a valid dish cost zero, so price
    readiness is checked per regular ingredient instead of via dish total.
    """
    return (
        bool(candidate.ingredient_ids)
        and len(candidate.ingredient_ids) == len(candidate.ingredients)
        and candidate.calories > 0
        and candidate.estimated_cost >= 0
        and all(
            ingredient.quantity > 0
            and ingredient.estimated_cost >= 0
            and (
                ingredient.purchase_mode != "regular"
                or ingredient.price_per_default_unit is None
                or ingredient.price_per_default_unit >= 0
            )
            for ingredient in candidate.ingredients
        )
    )


def candidate_is_eligible(candidate: DishCandidate, excluded: set[int]) -> bool:
    return has_valid_data(candidate) and not any(
        ingredient_id in excluded for ingredient_id in candidate.ingredient_ids
    )


def validate_plan(days: list[list[ComposedMeal]], request: PlanRequest) -> ValidationResult:
    violations: list[str] = []
    expected_slots = slots_for(request.meals_per_day)
    excluded = set(request.excluded_ingredient_ids)
    if len(days) != request.days:
        violations.append(f"HC-04: thực đơn có {len(days)} ngày, yêu cầu {request.days} ngày.")

    total_cost = 0.0
    for day_index, day in enumerate(days, start=1):
        if len(day) != len(expected_slots):
            violations.append(
                f"HC-05: ngày {day_index} có {len(day)} bữa, yêu cầu {len(expected_slots)} bữa."
            )
        for slot_index, meal in enumerate(day):
            total_cost += meal.estimated_cost
            expected = expected_slots[slot_index] if slot_index < len(expected_slots) else None
            if expected is not None and meal.slot != expected:
                violations.append(
                    f"HC-06: ngày {day_index} slot {slot_index + 1} là '{meal.slot.value}', cần '{expected.value}'."
                )
            if not valid_meal_types(meal):
                violations.append(
                    f"HC-COMPOSITION: ngày {day_index} bữa '{meal.slot.value}' không đúng cấu trúc dish bắt buộc."
                )
            dish_ids = [dish.dish_id for dish in meal.dishes]
            if len(dish_ids) != len(set(dish_ids)):
                violations.append(
                    f"HC-NO-DUPLICATE: ngày {day_index} bữa '{meal.slot.value}' có dish trùng lặp."
                )
            for dish in meal.dishes:
                if dish.dish_type == DishType.SIDE:
                    violations.append(f"HC-COMPOSITION: dish '{dish.name}' loại side chưa hỗ trợ planner.")
                if excluded and any(iid in excluded for iid in dish.ingredient_ids):
                    violations.append(
                        f"HC-02/03: ngày {day_index} dish '{dish.name}' chứa nguyên liệu bị loại trừ."
                    )
                if not has_valid_data(dish):
                    violations.append(f"HC-07: ngày {day_index} dish '{dish.name}' thiếu dữ liệu đầy đủ.")

    if request.budget_limit is not None and total_cost > request.budget_limit + 1e-6:
        violations.append(
            f"HC-01: tổng chi phí {total_cost:.0f}đ vượt ngân sách {request.budget_limit:.0f}đ."
        )
    if violations:
        return ValidationResult(status="infeasible", hard_violations=violations)
    return ValidationResult(status="valid")

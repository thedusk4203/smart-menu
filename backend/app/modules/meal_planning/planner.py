from __future__ import annotations

from dataclasses import asdict
from datetime import date, timedelta

from app.modules.meal_planning import constraint_checker, scorer
from app.modules.meal_planning.domain import (
    MealCandidate,
    MealPlanEntity,
    PlannedDay,
    PlannedMeal,
    PlanRequest,
    ValidationResult,
)
from app.modules.meal_planning.ports import MealPlannerPort
from app.modules.meal_planning.scorer import DEFAULT_WEIGHTS, ScoringWeights

# Cảnh báo mềm khi tổng calo/ngày lệch quá ngưỡng so với mục tiêu.
_CALORIE_WARN_TOLERANCE = 0.25


class HeuristicPlanner(MealPlannerPort):
    """Sinh thực đơn bằng greedy + chấm điểm soft-constraint."""

    def __init__(self, weights: ScoringWeights = DEFAULT_WEIGHTS) -> None:
        # Bộ trọng số soft-constraint (review D-06) — có thể inject để thử
        # nghiệm chiến lược khác (ưu tiên tiết kiệm, đa dạng...).
        self._weights = weights

    def generate(
        self,
        request: PlanRequest,
        candidates: list[MealCandidate],
        *,
        start_date: date | None = None,
    ) -> MealPlanEntity | ValidationResult:
        slots = constraint_checker.slots_for(request.meals_per_day)

        excluded = set(request.excluded_ingredient_ids)

        by_slot: dict[str, list[MealCandidate]] = {slot: [] for slot in slots}
        for slot in by_slot:
            by_slot[slot] = [
                c for c in candidates
                if constraint_checker.candidate_is_eligible(c, slot, excluded)
            ]

        # Tiền kiểm tính khả thi: thiếu món cho bất kỳ slot nào -> bất khả thi.
        empty_slots = [slot for slot, pool in by_slot.items() if not pool]
        if empty_slots:
            return ValidationResult(
                status="infeasible",
                infeasible_reasons=[
                    f"Không có món hợp lệ cho bữa '{slot}' (sau khi loại trừ dị ứng/"
                    f"thực phẩm không ăn và lọc dữ liệu thiếu)."
                    for slot in empty_slots
                ],
            )

        # max_cost để chuẩn hoá điểm "tiết kiệm" (SC-06) — trên toàn pool hợp lệ.
        max_cost = max(c.estimated_cost for pool in by_slot.values() for c in pool)

        usage_count: dict[int, int] = {}
        remaining_budget = (
            request.budget_limit if request.budget_limit is not None else float("inf")
        )
        days: list[list[MealCandidate]] = []

        for _day in range(request.days):
            day_meals: list[MealCandidate] = []
            day_ingredient_ids: set[int] = set()

            for slot in slots:
                pick = self._pick_for_slot(
                    pool=by_slot[slot],
                    request=request,
                    usage_count=usage_count,
                    day_ingredient_ids=day_ingredient_ids,
                    max_cost=max_cost,
                    remaining_budget=remaining_budget,
                )
                if pick is None:
                    # Không còn món nào nằm trong ngân sách còn lại -> bất khả thi.
                    return ValidationResult(
                        status="infeasible",
                        infeasible_reasons=[
                            f"Hết ngân sách trước khi xếp đủ bữa '{slot}' "
                            f"(còn {remaining_budget:.0f}đ). Hãy tăng ngân sách hoặc "
                            f"giảm số ngày/số bữa."
                        ],
                    )
                day_meals.append(pick)
                day_ingredient_ids.update(pick.ingredient_ids)
                usage_count[pick.meal_id] = usage_count.get(pick.meal_id, 0) + 1
                remaining_budget -= pick.estimated_cost

            days.append(day_meals)

        #validate toàn bộ thực đơn theo hard constraints ---
        validation = constraint_checker.validate_plan(days, request)
        if not validation.is_feasible:
            return validation

        # --- Bước 9: dựng MealPlanEntity + gắn cảnh báo mềm ---
        warnings = self._collect_warnings(days, request)
        return self._build_entity(days, request, start_date, warnings)

    def _pick_for_slot(
        self,
        *,
        pool: list[MealCandidate],
        request: PlanRequest,
        usage_count: dict[int, int],
        day_ingredient_ids: set[int],
        max_cost: float,
        remaining_budget: float,
    ) -> MealCandidate | None:
        """Trả món điểm cao nhất còn nằm trong ngân sách còn lại; None nếu
        không còn món nào đủ rẻ (HC-01 ở mức ghép động)."""
        affordable = [c for c in pool if c.estimated_cost <= remaining_budget]
        if not affordable:
            return None
        return max(
            affordable,
            key=lambda c: scorer.score_candidate(
                c,
                request,
                usage_count=usage_count,
                day_ingredient_ids=day_ingredient_ids,
                max_cost=max_cost,
                weights=self._weights,
            ),
        )


    def _collect_warnings(
        self, days: list[list[MealCandidate]], request: PlanRequest
    ) -> list[str]:
        warnings: list[str] = []
        if request.target_calories > 0:
            for i, day in enumerate(days, start=1):
                day_cal = sum(m.total_calories for m in day)
                deviation = abs(day_cal - request.target_calories) / request.target_calories
                if deviation > _CALORIE_WARN_TOLERANCE:
                    warnings.append(
                        f"Ngày {i}: tổng calo {day_cal:.0f} lệch {deviation * 100:.0f}% "
                        f"so với mục tiêu {request.target_calories:.0f} kcal."
                    )
        return warnings


    def _build_entity(
        self,
        days: list[list[MealCandidate]],
        request: PlanRequest,
        start_date: date | None,
        warnings: list[str],
    ) -> MealPlanEntity:
        plan_days = []
        total_cost = 0.0
        total_calories = 0.0
        for i, day in enumerate(days):
            day_date = (start_date + timedelta(days=i)).isoformat() if start_date else None
            day_cost = sum(m.estimated_cost for m in day)
            day_cal = sum(m.total_calories for m in day)
            total_cost += day_cost
            total_calories += day_cal
            # Dựng theo dataclass (review D-10) rồi asdict() -> JSON nguyên dạng cũ.
            planned_day = PlannedDay(
                day=i + 1,
                date=day_date,
                meals=[
                    PlannedMeal(
                        meal_id=m.meal_id,
                        name=m.name,
                        meal_type=m.meal_type,
                        calories=round(m.total_calories, 1),
                        protein_g=round(m.total_protein_g, 1),
                        fat_g=round(m.total_fat_g, 1),
                        carb_g=round(m.total_carb_g, 1),
                        cost=round(m.estimated_cost, 0),
                    )
                    for m in day
                ],
                day_calories=round(day_cal, 1),
                day_cost=round(day_cost, 0),
            )
            plan_days.append(asdict(planned_day))

        end_date = (
            start_date + timedelta(days=request.days - 1) if start_date else None
        )
        return MealPlanEntity(
            id=None,
            user_id=request.user_id,
            start_date=start_date,
            end_date=end_date,
            budget_limit=request.budget_limit,
            total_cost=round(total_cost, 0),
            total_calories=round(total_calories, 1),
            plan_data={
                "days": plan_days,
                "warnings": warnings,
                "meals_per_day": request.meals_per_day,
            },
        )

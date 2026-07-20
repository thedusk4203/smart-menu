from __future__ import annotations

from dataclasses import asdict, replace
from datetime import date, timedelta

from app.modules.meal_planning import constraint_checker, feasibility, procurement_checker
from app.modules.meal_planning.composition import canonical_dishes_for_meal
from app.modules.meal_planning.domain import (
    ComposedMeal,
    DishCandidate,
    InfeasibleReason,
    MealPlanEntity,
    PlanMetrics,
    PlannedDay,
    PlannedMeal,
    PlanRequest,
    QualityPolicy,
    StructuredWarning,
    ValidationResult,
)
from app.modules.meal_planning.optimizer_contracts import V3OptimizationResult
from app.modules.meal_planning.optimizer_v3 import ProcurementCpSatOptimizer
from app.modules.meal_planning.ports import MealPlannerPort
from app.modules.meal_planning.quality import DEFAULT_QUALITY_POLICY


class DishPlanner(MealPlannerPort):
    """Orchestrator duy nhất của Dish Planner V3."""

    def __init__(
        self,
        policy: QualityPolicy = DEFAULT_QUALITY_POLICY,
    ) -> None:
        self._policy = policy
        self._optimizer = ProcurementCpSatOptimizer(policy)

    def generate(
        self,
        request: PlanRequest,
        candidates: list[DishCandidate],
        *,
        start_date: date | None = None,
        seed: int | None = None,
    ) -> MealPlanEntity | ValidationResult:
        excluded = set(request.excluded_ingredient_ids)
        eligible = [
            candidate
            for candidate in candidates
            if constraint_checker.candidate_is_eligible(candidate, excluded)
        ]
        missing = {
            ingredient.ingredient_id
            for candidate in eligible for ingredient in candidate.ingredients
            if not ingredient.procurement_ready
        }
        if missing:
            return ValidationResult(
                status="infeasible",
                infeasible_reasons=[
                    InfeasibleReason(
                        "MISSING_PURCHASE_RULE",
                        "Catalog chưa có đủ bước mua hoặc giá chuẩn hóa cho Planner V3.",
                        {"ingredient_count": len(missing)},
                    )
                ],
            )
        precheck = feasibility.assess(eligible, request)
        if not precheck.is_feasible:
            return ValidationResult(
                status="infeasible",
                infeasible_reasons=precheck.infeasible_reasons,
                warnings=precheck.warnings,
            )
        solved = self._optimizer.solve(request, eligible, seed=seed)
        without_budget: V3OptimizationResult | None = None
        if solved is None and request.budget_limit is not None:
            # The procurement-heavy CP model can exhaust its search window on
            # a 7-day horizon before it finds an incumbent once a budget row is
            # present, even when that budget is far above the actual JIT cost.
            # Recover with the same nutrition/storage model without that row,
            # then enforce the real post-JIT purchase cost independently.
            without_budget = self._optimizer.solve(
                replace(request, budget_limit=None), eligible, seed=seed
            )
            if (
                without_budget is not None
                and without_budget.purchase_cost <= request.budget_limit + 1e-6
            ):
                solved = replace(
                    without_budget,
                    source_fingerprint=self._optimizer.source_fingerprint(
                        request, without_budget.days
                    ),
                    warnings=[
                        *without_budget.warnings,
                        StructuredWarning(
                            "BUDGET_SEARCH_TIMEOUT_RECOVERED",
                            "Đã khôi phục nghiệm 7 ngày và kiểm tra lại chi phí mua thực tế trong ngân sách.",
                            {
                                "budget_limit": round(float(request.budget_limit)),
                                "purchase_cost": round(without_budget.purchase_cost),
                            },
                        ),
                    ],
                )
        if solved is None:
            return self._diagnose_v3_failure(
                request, eligible, seed, without_budget=without_budget
            )
        selected_candidates = list({
            dish.dish_id: dish
            for day in solved.days for meal in day for dish in meal.dishes
        }.values())
        refined = self._optimizer.solve(
            request,
            selected_candidates,
            seed=seed,
            fixed_days=solved.days,
        )
        if refined is not None:
            solved = refined
        validation = procurement_checker.validate_v3(solved, request)
        if not validation.is_feasible:
            return validation

        warnings = list(precheck.warnings)
        warnings.extend(solved.warnings)
        return self.build_entity(solved.days, request, start_date, warnings, solved)

    def _diagnose_v3_failure(
        self,
        request: PlanRequest,
        candidates: list[DishCandidate],
        seed: int | None,
        *,
        without_budget: V3OptimizationResult | None = None,
    ) -> ValidationResult:
        """Separate purchase-block budget conflicts from nutrition/storage conflicts."""
        if request.budget_limit is not None:
            if without_budget is None:
                without_budget = self._optimizer.solve(
                    replace(request, budget_limit=None), candidates, seed=seed
                )
            if isinstance(without_budget, V3OptimizationResult):
                minimum_cost = without_budget.purchase_cost
                if minimum_cost > request.budget_limit + 1e-6:
                    return ValidationResult(
                        status="infeasible",
                        infeasible_reasons=[
                            InfeasibleReason(
                                "BUDGET_PURCHASE_BLOCK_CONFLICT",
                                "Ngân sách không đủ cho các block mua tối thiểu của một thực đơn đạt dinh dưỡng.",
                                {
                                    "budget_limit": round(float(request.budget_limit)),
                                    "minimum_feasible_purchase_cost": round(minimum_cost),
                                    "budget_gap": round(minimum_cost - request.budget_limit),
                                },
                            )
                        ],
                    )
                return ValidationResult(
                    status="infeasible",
                    infeasible_reasons=[
                        InfeasibleReason(
                            "SOLVER_SEARCH_TIMEOUT",
                            "Solver hết thời gian tìm kiếm trước khi dựng được nghiệm 7 ngày đã kiểm chứng.",
                            {
                                "budget_limit": round(float(request.budget_limit)),
                                "verified_purchase_cost": round(minimum_cost),
                            },
                        )
                    ],
                )
        return ValidationResult(
            status="infeasible",
            infeasible_reasons=[
                InfeasibleReason(
                    "NUTRITION_STORAGE_CONFLICT",
                    "Không thể đồng thời đạt biên dinh dưỡng và cấp nguyên liệu trong hạn bảo quản.",
                )
            ],
        )

    def build_entity(
        self,
        days: list[list[ComposedMeal]],
        request: PlanRequest,
        start_date: date | None,
        warnings: list[StructuredWarning],
        solved,
    ) -> MealPlanEntity:
        if isinstance(solved, V3OptimizationResult):
            return self._build_entity_v3(days, request, start_date, warnings, solved)
        raise TypeError("Planner V3 chỉ chấp nhận V3OptimizationResult")
    def _build_entity_v3(
        self,
        days: list[list[ComposedMeal]],
        request: PlanRequest,
        start_date: date | None,
        warnings: list[StructuredWarning],
        solved: V3OptimizationResult,
    ) -> MealPlanEntity:
        adjustment_lookup = {
            (
                int(item["day"]),
                str(item["slot"]),
                int(item["dish_id"]),
                int(item["ingredient_id"]),
            ): item
            for item in solved.adjustments
        }
        plan_days: list[dict] = []
        signature_parts: list[str] = []
        for day_index, meals in enumerate(days, start=1):
            planned_meals: list[PlannedMeal] = []
            for meal in meals:
                dish_snapshots: list[dict] = []
                for dish in canonical_dishes_for_meal(meal):
                    signature_parts.append(f"{day_index}:{meal.slot.value}:{dish.dish_id}")
                    ingredient_snapshots: list[dict] = []
                    dish_delta = {"calories": 0.0, "protein_g": 0.0, "fat_g": 0.0, "carb_g": 0.0}
                    dish_value = 0.0
                    for ingredient in dish.ingredients:
                        adjustment = adjustment_lookup.get(
                            (day_index, meal.slot.value, dish.dish_id, ingredient.ingredient_id)
                        )
                        extra = float(adjustment["extra_quantity"]) if adjustment else 0.0
                        actual = ingredient.quantity + extra
                        delta = ingredient.nutrition_for(extra)
                        for key in dish_delta:
                            dish_delta[key] += delta[key]
                        estimated_value = (
                            actual * float(ingredient.price_per_default_unit or 0)
                            if ingredient.purchase_mode == "regular" else 0.0
                        )
                        dish_value += estimated_value
                        snapshot = asdict(ingredient)
                        snapshot.update({
                            "quantity": round(actual, 2),
                            "base_quantity": round(ingredient.quantity, 2),
                            "extra_quantity": round(extra, 2),
                            "actual_quantity": round(actual, 2),
                            "estimated_cost": round(estimated_value, 0),
                            "adjustment_reason": "leftover_absorption" if extra else None,
                            "nutrition_delta": {key: round(value, 2) for key, value in delta.items()},
                        })
                        ingredient_snapshots.append(snapshot)
                    dish_snapshots.append({
                        "dish_id": dish.dish_id,
                        "name": dish.name,
                        "dish_type": dish.dish_type.value,
                        "cooking_method": dish.cooking_method.value if dish.cooking_method else None,
                        "calories": round(dish.calories + dish_delta["calories"], 1),
                        "protein_g": round(dish.protein_g + dish_delta["protein_g"], 1),
                        "fat_g": round(dish.fat_g + dish_delta["fat_g"], 1),
                        "carb_g": round(dish.carb_g + dish_delta["carb_g"], 1),
                        "cost": round(dish_value, 0),
                        "estimated_consumption_value": round(dish_value, 0),
                        "tags": list(dish.tags),
                        "ingredients": ingredient_snapshots,
                    })
                meal_totals = {
                    key: sum(float(dish[key]) for dish in dish_snapshots)
                    for key in ("calories", "protein_g", "fat_g", "carb_g")
                }
                meal_value = sum(float(dish["estimated_consumption_value"]) for dish in dish_snapshots)
                planned_meals.append(
                    PlannedMeal(
                        name=" · ".join(dish["name"] for dish in dish_snapshots),
                        meal_type=meal.slot.value,
                        components=[dish["name"] for dish in dish_snapshots],
                        calories=round(meal_totals["calories"], 1),
                        protein_g=round(meal_totals["protein_g"], 1),
                        fat_g=round(meal_totals["fat_g"], 1),
                        carb_g=round(meal_totals["carb_g"], 1),
                        cost=round(meal_value, 0),
                        dishes=dish_snapshots,
                    )
                )
            final_day = solved.final_nutrition[day_index - 1]
            day_value = sum(meal.cost for meal in planned_meals)
            plan_days.append(
                asdict(
                    PlannedDay(
                        day=day_index,
                        date=(start_date + timedelta(days=day_index - 1)).isoformat()
                        if start_date else None,
                        meals=planned_meals,
                        day_calories=round(final_day["calories"], 1),
                        day_cost=round(day_value, 0),
                    )
                )
            )

        cost_summary = solved.procurement_plan["cost_summary"]
        metrics = asdict(self._metrics(days, request, solved.solver_time_ms, solved.nutrition_score))
        calories = [float(day["calories"]) for day in solved.final_nutrition]
        deviations = [
            abs(value - request.target_calories) / request.target_calories * 100
            for value in calories
        ] if request.target_calories else []
        protein = sum(float(day["protein_g"]) for day in solved.final_nutrition)
        protein_target = request.target_protein_g * request.days
        metrics.update({
            "average_calorie_deviation_pct": round(sum(deviations) / len(deviations), 1)
            if deviations else 0.0,
            "maximum_calorie_deviation_pct": round(max(deviations), 1) if deviations else 0.0,
            "protein_shortage_pct": round(max(0.0, protein_target - protein) / protein_target * 100, 1)
            if protein_target else 0.0,
            "purchase_cost": cost_summary["purchase_cost"],
            "consumption_value": cost_summary["consumption_value"],
            "expired_waste_value": cost_summary["expired_waste_value"],
            "ending_carryover_value": cost_summary["ending_carryover_value"],
            "shopping_days": len(solved.procurement_plan["shopping_days"]),
        })
        end_date = start_date + timedelta(days=request.days - 1) if start_date else None
        total_calories = sum(float(day["calories"]) for day in solved.final_nutrition)
        return MealPlanEntity(
            id=None,
            user_id=request.user_id,
            start_date=start_date,
            end_date=end_date,
            budget_limit=request.budget_limit,
            total_cost=float(cost_summary["purchase_cost"]),
            total_calories=round(total_calories, 1),
            plan_data={
                "schema_version": 3,
                "algorithm_version": "dish-cpsat-procurement-v3-jit2",
                "source_fingerprint": solved.source_fingerprint,
                "plan_signature": "|".join(signature_parts),
                "solver_status": solved.solver_status,
                "diversity_tier": solved.diversity_tier,
                "request_snapshot": {
                    "days": request.days,
                    "meals_per_day": request.meals_per_day,
                    "budget_limit": request.budget_limit,
                    "start_date": start_date.isoformat() if start_date else None,
                    "excluded_ingredient_ids": sorted(set(request.excluded_ingredient_ids)),
                    "preferred_tags": list(request.preferred_tags),
                },
                "nutrition_target": {
                    "calories": request.target_calories,
                    "protein_g": request.target_protein_g,
                    "fat_g": request.target_fat_g,
                    "carb_g": request.target_carb_g,
                },
                "base_nutrition": solved.base_nutrition,
                "final_nutrition": solved.final_nutrition,
                "cost_summary": cost_summary,
                "procurement": solved.procurement_plan,
                "adjustments": solved.adjustments,
                "days": plan_days,
                "metrics": metrics,
                "warnings": [asdict(warning) for warning in warnings],
                "meals_per_day": request.meals_per_day,
            },
        )

    @staticmethod
    def _metrics(
        days: list[list[ComposedMeal]],
        request: PlanRequest,
        solver_time_ms: int,
        nutrition_score: int,
    ) -> PlanMetrics:
        calories = [sum(meal.calories for meal in day) for day in days]
        deviations = [
            abs(value - request.target_calories) / request.target_calories * 100
            for value in calories
        ] if request.target_calories else []
        total_protein = sum(meal.protein_g for day in days for meal in day)
        total_protein_target = request.target_protein_g * request.days
        protein_shortage = max(0.0, total_protein_target - total_protein)
        type_counts: dict[str, dict[int, int]] = {}
        for day in days:
            for meal in day:
                for dish in meal.dishes:
                    counts = type_counts.setdefault(dish.dish_type.value, {})
                    counts[dish.dish_id] = counts.get(dish.dish_id, 0) + 1
        repeat_counts = {
            ("side" if dish_type in {"soup", "vegetable_side"} else dish_type): 0
            for dish_type in type_counts
        }
        for dish_type, counts in type_counts.items():
            key = "side" if dish_type in {"soup", "vegetable_side"} else dish_type
            repeat_counts[key] = repeat_counts.get(key, 0) + sum(max(0, count - 1) for count in counts.values())
        return PlanMetrics(
            average_calorie_deviation_pct=round(sum(deviations) / len(deviations), 1) if deviations else 0.0,
            maximum_calorie_deviation_pct=round(max(deviations), 1) if deviations else 0.0,
            protein_shortage_pct=round(protein_shortage / total_protein_target * 100, 1) if total_protein_target else 0.0,
            repeat_counts=repeat_counts,
            solver_time_ms=solver_time_ms,
            nutrition_score=nutrition_score,
        )

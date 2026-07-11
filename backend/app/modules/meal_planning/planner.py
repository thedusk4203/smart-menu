from __future__ import annotations

from dataclasses import asdict
from datetime import date, timedelta

from app.modules.meal_planning import constraint_checker, feasibility
from app.modules.meal_planning.composition import canonical_dishes_for_meal
from app.modules.meal_planning.domain import (
    ComposedMeal,
    DishCandidate,
    InfeasibleReason,
    MealPlanEntity,
    PlanMetrics,
    PlannedDay,
    PlannedMeal,
    PlannerMetadata,
    PlanRequest,
    QualityPolicy,
    StructuredWarning,
    ValidationResult,
)
from app.modules.meal_planning.optimizer import DishCpSatOptimizer
from app.modules.meal_planning.ports import MealPlannerPort
from app.modules.meal_planning.quality import DEFAULT_QUALITY_POLICY


class DishPlanner(MealPlannerPort):
    """Orchestrator Dish Planner V2: data → precheck → CP-SAT → checker."""

    def __init__(self, policy: QualityPolicy = DEFAULT_QUALITY_POLICY) -> None:
        self._policy = policy
        self._optimizer = DishCpSatOptimizer(policy)

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
        precheck = feasibility.assess(eligible, request)
        if not precheck.is_feasible:
            return ValidationResult(
                status="infeasible",
                infeasible_reasons=precheck.infeasible_reasons,
                warnings=precheck.warnings,
            )
        solved = self._optimizer.solve(request, eligible, seed=seed)
        if solved is None:
            return ValidationResult(
                status="infeasible",
                infeasible_reasons=[
                    # Precheck has established role/budget feasibility. Solver failure
                    # therefore remains explicit instead of claiming lack of candidates.
                    InfeasibleReason(
                        "SOLVER_NO_FEASIBLE_SOLUTION",
                        "Không tìm được nghiệm hợp lệ trong giới hạn solver.",
                    )
                ],
                warnings=precheck.warnings,
            )
        validation = constraint_checker.validate_plan(solved.days, request)
        if not validation.is_feasible:
            return validation

        warnings = list(precheck.warnings)
        if solved.timed_out_with_solution:
            warnings.append(
                StructuredWarning(
                    "SOLVER_TIMEOUT_BEST_EFFORT",
                    "Solver hết thời gian nhưng đã trả nghiệm hợp lệ tốt nhất tìm được.",
                    {"solver_time_ms": solved.solver_time_ms},
                )
            )
        return self.build_entity(solved.days, request, start_date, warnings, solved)

    def build_entity(
        self,
        days: list[list[ComposedMeal]],
        request: PlanRequest,
        start_date: date | None,
        warnings: list[StructuredWarning],
        solved,
    ) -> MealPlanEntity:
        plan_days: list[dict] = []
        total_cost = 0.0
        total_calories = 0.0
        signature_parts: list[str] = []
        for day_index, meals in enumerate(days, start=1):
            day_date = (start_date + timedelta(days=day_index - 1)).isoformat() if start_date else None
            day_cost = sum(meal.estimated_cost for meal in meals)
            day_calories = sum(meal.calories for meal in meals)
            total_cost += day_cost
            total_calories += day_calories
            planned_meals: list[PlannedMeal] = []
            for meal in meals:
                dishes = canonical_dishes_for_meal(meal)
                signature_parts.extend(f"{day_index}:{meal.slot.value}:{dish.dish_id}" for dish in dishes)
                dish_snapshots = [
                    {
                        "dish_id": dish.dish_id,
                        "name": dish.name,
                        "dish_type": dish.dish_type.value,
                        "cooking_method": dish.cooking_method.value if dish.cooking_method else None,
                        "calories": round(dish.calories, 1),
                        "protein_g": round(dish.protein_g, 1),
                        "fat_g": round(dish.fat_g, 1),
                        "carb_g": round(dish.carb_g, 1),
                        "cost": round(dish.estimated_cost, 0),
                        "tags": list(dish.tags),
                        "ingredients": [asdict(ingredient) for ingredient in dish.ingredients],
                    }
                    for dish in dishes
                ]
                planned_meals.append(
                    PlannedMeal(
                        name=" · ".join(dish.name for dish in dishes),
                        meal_type=meal.slot.value,
                        components=[dish.name for dish in dishes],
                        calories=round(meal.calories, 1),
                        protein_g=round(meal.protein_g, 1),
                        fat_g=round(meal.fat_g, 1),
                        carb_g=round(meal.carb_g, 1),
                        cost=round(meal.estimated_cost, 0),
                        dishes=dish_snapshots,
                    )
                )
            plan_days.append(
                asdict(
                    PlannedDay(
                        day=day_index,
                        date=day_date,
                        meals=planned_meals,
                        day_calories=round(day_calories, 1),
                        day_cost=round(day_cost, 0),
                    )
                )
            )
        metrics = self._metrics(days, request, solved.solver_time_ms, solved.nutrition_score)
        metadata = PlannerMetadata(
            plan_signature="|".join(signature_parts),
            solver_status=solved.solver_status,
        )
        end_date = start_date + timedelta(days=request.days - 1) if start_date else None
        return MealPlanEntity(
            id=None,
            user_id=request.user_id,
            start_date=start_date,
            end_date=end_date,
            budget_limit=request.budget_limit,
            total_cost=round(total_cost, 0),
            total_calories=round(total_calories, 1),
            plan_data={
                "schema_version": 2,
                "algorithm_version": metadata.algorithm_version,
                "plan_signature": metadata.plan_signature,
                "solver_status": metadata.solver_status,
                "request_snapshot": {
                    "days": request.days,
                    "meals_per_day": request.meals_per_day,
                    "budget_limit": request.budget_limit,
                    "excluded_ingredient_ids": sorted(set(request.excluded_ingredient_ids)),
                    "preferred_tags": list(request.preferred_tags),
                },
                "nutrition_target": {
                    "calories": request.target_calories,
                    "protein_g": request.target_protein_g,
                    "fat_g": request.target_fat_g,
                    "carb_g": request.target_carb_g,
                },
                "days": plan_days,
                "metrics": asdict(metrics),
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

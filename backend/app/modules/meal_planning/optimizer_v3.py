"""Procurement-aware CP-SAT optimizer for Meal Planner schema V3.

The model selects dishes and the actual purchase blocks in one solve. Raw
ingredient stock exists only inside the current 1-7 day horizon; pantry and
ignored ingredients still contribute nutrition but do not create purchase
variables.
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR
from typing import Any

from ortools.sat.python import cp_model

from app.modules.meal_planning.candidate_selector import CandidateSelector, add_regenerate_difference
from app.modules.meal_planning.composition import canonical_dishes_for_meal, slots_for
from app.modules.meal_planning.domain import (
    ComposedMeal,
    DishCandidate,
    DishIngredientSnapshot,
    PlanRequest,
    QualityPolicy,
    StructuredWarning,
)
from app.modules.meal_planning.jit_scheduler import JitProcurementScheduler
from app.modules.meal_planning.optimizer_contracts import V3OptimizationResult
from app.modules.meal_planning.plan_fingerprint import source_fingerprint
from app.modules.meal_planning.procurement_ledger import build_daily_ledger
from app.modules.meal_planning.quality import DEFAULT_QUALITY_POLICY
from app.shared.enums import DishType, MealType


_Q_SCALE = 100
_N_SCALE = 100
_VALUE_SCALE = 100  # centi-VND so sub-VND normalized prices remain ordered


def _scaled_floor(value: float, *factors: float | int) -> int:
    scaled = Decimal(str(value))
    for factor in factors:
        scaled *= Decimal(str(factor))
    return int((scaled * _N_SCALE).to_integral_value(rounding=ROUND_FLOOR))


def _scaled_ceil(value: float, *factors: float | int) -> int:
    scaled = Decimal(str(value))
    for factor in factors:
        scaled *= Decimal(str(factor))
    return int((scaled * _N_SCALE).to_integral_value(rounding=ROUND_CEILING))


@dataclass
class _ModelData:
    model: cp_model.CpModel
    candidates: list[DishCandidate]
    ingredients: dict[int, DishIngredientSnapshot]
    x: dict[tuple[int, MealType, int], cp_model.IntVar]
    buy: dict[tuple[int, int], cp_model.IntVar]
    allocation: dict[tuple[int, int, int], cp_model.IntVar]
    unused: dict[tuple[int, int], cp_model.IntVar]
    inventory_allocation: dict[tuple[int, int], cp_model.IntVar]
    inventory_unused: dict[int, cp_model.IntVar]
    shopping_days: dict[int, cp_model.IntVar]
    nutrition_score: cp_model.IntVar
    purchase_cost: cp_model.LinearExpr
    expired_value: cp_model.LinearExpr
    carryover_value: cp_model.LinearExpr
    stock_rotation: cp_model.LinearExpr
    holding_quantity_days: cp_model.LinearExpr
    quality_score: cp_model.LinearExpr


@dataclass(frozen=True)
class _Captured:
    x: dict[tuple[int, MealType, int], int]
    buy: dict[tuple[int, int], int]
    allocation: dict[tuple[int, int, int], int]
    unused: dict[tuple[int, int], int]
    inventory_allocation: dict[tuple[int, int], int]
    inventory_unused: dict[int, int]
    nutrition_score: int
    purchase_cost: int
    expired_value: int
    carryover_value: int
    stock_rotation: int
    holding_quantity_days: int
    shopping_days: int
    status_name: str


class ProcurementCpSatOptimizer:
    """Lexicographic dish/procurement optimizer with verified incumbents."""

    DIVERSITY_TIERS = ("adequate", "no_consecutive", "raised_cap", "soft_only")

    def __init__(
        self,
        policy: QualityPolicy = DEFAULT_QUALITY_POLICY,
        timeout_seconds: float = 4.5,
    ) -> None:
        self._policy = policy
        self._timeout_seconds = timeout_seconds
        self._selector = CandidateSelector(policy)

    def solve(
        self,
        request: PlanRequest,
        candidates: list[DishCandidate],
        *,
        seed: int | None = None,
        fixed_days: list[list[ComposedMeal]] | None = None,
    ) -> V3OptimizationResult | None:
        started = time.perf_counter()
        eligible = [candidate for candidate in candidates if self._procurement_ready(candidate)]
        if not eligible:
            return None
        eligible = self._selector.shortlist(
            request, sorted(eligible, key=lambda item: item.dish_id)
        )

        selected_data: _ModelData | None = None
        captured: _Captured | None = None
        selected_tier = "soft_only"
        phase_complete: list[str] = []
        # Establish a least-restrictive incumbent first. Seven-day catalogs can
        # spend the entire time limit proving the strict repeat caps infeasible;
        # without this baseline the valid relaxed tier is never reached.
        tiers = (
            ("soft_only",)
            if fixed_days is not None
            else ("soft_only", *self.DIVERSITY_TIERS[:-1])
        )
        for tier_index, tier in enumerate(tiers):
            remaining = self._remaining(started)
            if remaining <= 0:
                break
            data = self._build_model(request, eligible, tier)
            if fixed_days is not None:
                selected = {
                    (day_index, meal.slot, dish.dish_id)
                    for day_index, day in enumerate(fixed_days)
                    for meal in day for dish in meal.dishes
                }
                for key, variable in data.x.items():
                    data.model.Add(variable == int(key in selected))
            add_regenerate_difference(data.model, data.x, request.previous_plan_signature)
            data.model.Minimize(data.nutrition_score)
            phase_timeout = self._initial_phase_timeout(
                tier, tier_index, tiers, remaining
            )
            solver = self._solver(seed, phase_timeout)
            status = solver.Solve(data.model)
            if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
                selected_data = data
                captured = self._capture(data, solver, status)
                selected_tier = tier
                if not phase_complete:
                    phase_complete.append("nutrition")
                tight_budget_incumbent = (
                    tier == "soft_only"
                    and request.budget_limit is not None
                    and captured.purchase_cost >= request.budget_limit * 0.95
                )
                if (
                    fixed_days is not None
                    or tier != "soft_only"
                    or tight_budget_incumbent
                ):
                    break
        if selected_data is None or captured is None:
            return None

        data = selected_data
        timed_out = captured.status_name != "OPTIMAL"

        # Actual purchase cost is optimized only inside a narrow band around
        # the best nutrition score found for the selected diversity tier.
        nutrition_limit = captured.nutrition_score + math.ceil(
            captured.nutrition_score * self._policy.quality_nutrition_slack_pct / 100
        )
        data.model.Add(data.nutrition_score <= nutrition_limit)
        trips_expr = sum(data.shopping_days.values())
        # Lock every higher-priority optimum before optimizing the next phase.
        # Waste and carry-over are budget outcomes, so they outrank shopping
        # convenience. Holding time runs after the trip count is fixed and
        # chooses the latest feasible purchase on those same shopping days.
        phases = (
            (data.purchase_cost, "purchase_cost", "purchase_cost"),
            (data.expired_value, "expired_waste", "expired_value"),
            (data.carryover_value, "carryover", "carryover_value"),
            (data.stock_rotation, "stock_rotation", "stock_rotation"),
            (trips_expr, "shopping_days", "shopping_days"),
            (data.holding_quantity_days, "holding_time", "holding_quantity_days"),
        )
        can_continue = True
        for objective, phase_name, captured_attribute in phases:
            incumbent_value = int(getattr(captured, captured_attribute))
            data.model.Add(objective <= incumbent_value)
            candidate, has_solution, proven_optimal = self._run_phase(
                data, captured, objective, phase_name, started, seed
            )
            if not has_solution:
                timed_out = True
                can_continue = False
                break
            captured = candidate
            timed_out |= not proven_optimal
            phase_complete.append(phase_name)
            data.model.Add(objective <= int(getattr(captured, captured_attribute)))

        if can_continue:
            captured, has_solution, proven_optimal = self._run_phase(
                data, captured, data.quality_score, "quality", started, seed
            )
            timed_out |= not has_solution or not proven_optimal
            if has_solution:
                phase_complete.append("soft_diversity")

        days = self._materialize_days(request, data.candidates, data.x, captured.x)
        procurement, adjustments, base_nutrition, final_nutrition = self._materialize_procurement(
            request, days, data.ingredients
        )
        warnings: list[StructuredWarning] = []
        if fixed_days is None and selected_tier != "adequate":
            warnings.append(
                StructuredWarning(
                    "DIVERSITY_RELAXED_FOR_FEASIBILITY",
                    "Đã nới một phần giới hạn lặp để giữ ngân sách và dinh dưỡng.",
                    {"tier": selected_tier},
                )
            )
        if timed_out:
            warnings.append(
                StructuredWarning(
                    "SOLVER_TIMEOUT_BEST_EFFORT",
                    "Đã trả nghiệm hợp lệ tốt nhất từ các pha hoàn tất.",
                    {"completed_phases": ",".join(phase_complete)},
                )
            )
        if any(
            ingredient.purchase_mode == "regular"
            and ingredient.room_shelf_life_days is None
            and ingredient.fridge_shelf_life_days is None
            and ingredient.freezer_shelf_life_days is None
            for ingredient in data.ingredients.values()
        ):
            warnings.append(
                StructuredWarning(
                    "MISSING_STORAGE_RULE_SAME_DAY_ONLY",
                    "Một số nguyên liệu chưa có hạn bảo quản nên chỉ được mua và dùng cùng ngày.",
                )
            )
        if procurement["pantry_checks"]:
            warnings.append(
                StructuredWarning(
                    "PANTRY_ASSUMED_AVAILABLE",
                    "Nguyên liệu pantry được giả định có sẵn và không tính vào ngân sách.",
                    {"ingredient_count": len(procurement["pantry_checks"])},
                )
            )

        fingerprint = self.source_fingerprint(request, days)
        return V3OptimizationResult(
            days=days,
            nutrition_score=self._nutrition_score(final_nutrition, request),
            solver_time_ms=int((time.perf_counter() - started) * 1000),
            solver_status=captured.status_name,
            timed_out_with_solution=timed_out,
            procurement_plan=procurement,
            adjustments=adjustments,
            base_nutrition=base_nutrition,
            final_nutrition=final_nutrition,
            warnings=warnings,
            diversity_tier=selected_tier,
            source_fingerprint=fingerprint,
        )

    def _remaining(self, started: float) -> float:
        return max(0.0, self._timeout_seconds - (time.perf_counter() - started))

    def _initial_phase_timeout(
        self,
        tier: str,
        tier_index: int,
        tiers: tuple[str, ...],
        remaining: float,
    ) -> float:
        """Budget initial feasibility first, then spend remaining time on diversity."""
        if len(tiers) == 1:
            return min(0.7, remaining)
        if tier_index == 0 and tier == "soft_only":
            return min(1.8, remaining)
        if tier == "raised_cap":
            return min(1.05, remaining)
        return min(0.55, remaining)

    def _run_phase(
        self,
        data: _ModelData,
        incumbent: _Captured,
        objective: cp_model.LinearExpr,
        _name: str,
        started: float,
        seed: int | None,
    ) -> tuple[_Captured, bool, bool]:
        remaining = self._remaining(started)
        if remaining <= 0.03:
            return incumbent, False, False
        data.model.Minimize(objective)
        solver = self._solver(seed, min(0.45, remaining))
        status = solver.Solve(data.model)
        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return incumbent, False, False
        return self._capture(data, solver, status), True, status == cp_model.OPTIMAL

    @staticmethod
    def _solver(seed: int | None, timeout: float) -> cp_model.CpSolver:
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = max(0.01, timeout)
        solver.parameters.num_search_workers = 1
        solver.parameters.random_seed = 0 if seed is None else seed
        return solver

    @staticmethod
    def _procurement_ready(candidate: DishCandidate) -> bool:
        return bool(candidate.ingredients) and all(
            ingredient.procurement_ready for ingredient in candidate.ingredients
        )

    def _build_model(
        self,
        request: PlanRequest,
        candidates: list[DishCandidate],
        diversity_tier: str,
    ) -> _ModelData:
        model = cp_model.CpModel()
        pools: dict[DishType, list[DishCandidate]] = {kind: [] for kind in DishType}
        for candidate in candidates:
            pools[candidate.dish_type].append(candidate)
        side_pool = pools[DishType.VEGETABLE_SIDE] + pools[DishType.SOUP]
        positions: list[tuple[int, MealType, list[DishCandidate]]] = []
        for day in range(request.days):
            for slot in slots_for(request.meals_per_day):
                if slot == MealType.BREAKFAST:
                    positions.append((day, slot, pools[DishType.BREAKFAST]))
                else:
                    positions.extend((
                        (day, slot, pools[DishType.STAPLE]),
                        (day, slot, pools[DishType.SAVORY]),
                        (day, slot, side_pool),
                    ))
        if any(not pool for _day, _slot, pool in positions):
            raise ValueError("Thiếu pool dish bắt buộc")

        x: dict[tuple[int, MealType, int], cp_model.IntVar] = {}
        for day, slot, pool in positions:
            variables = []
            for candidate in pool:
                key = (day, slot, candidate.dish_id)
                variable = x.get(key)
                if variable is None:
                    variable = model.NewBoolVar(f"x_{day}_{slot.value}_{candidate.dish_id}")
                    x[key] = variable
                variables.append(variable)
            model.AddExactlyOne(variables)

        values = {candidate.dish_id: candidate for candidate in candidates}
        ingredients: dict[int, DishIngredientSnapshot] = {}
        for candidate in candidates:
            for ingredient in candidate.ingredients:
                ingredients.setdefault(ingredient.ingredient_id, ingredient)

        demand: dict[tuple[int, int], cp_model.LinearExpr] = {}
        for ingredient_id in ingredients:
            for day in range(request.days):
                parts = []
                for (selected_day, _slot, dish_id), variable in x.items():
                    if selected_day != day:
                        continue
                    ingredient = next(
                        (item for item in values[dish_id].ingredients if item.ingredient_id == ingredient_id),
                        None,
                    )
                    if ingredient is not None:
                        parts.append(int(round(ingredient.quantity * _Q_SCALE)) * variable)
                demand[(ingredient_id, day)] = sum(parts) if parts else 0

        buy: dict[tuple[int, int], cp_model.IntVar] = {}
        allocation: dict[tuple[int, int, int], cp_model.IntVar] = {}
        unused: dict[tuple[int, int], cp_model.IntVar] = {}
        inventory_allocation: dict[tuple[int, int], cp_model.IntVar] = {}
        inventory_unused: dict[int, cp_model.IntVar] = {}
        shopping_days = {day: model.NewBoolVar(f"shopping_{day}") for day in range(request.days)}
        purchase_parts: list[cp_model.LinearExpr] = []
        expired_parts: list[cp_model.LinearExpr] = []
        carryover_parts: list[cp_model.LinearExpr] = []
        stock_rotation_parts: list[cp_model.LinearExpr] = []
        holding_parts: list[cp_model.LinearExpr] = []

        regular = {
            ingredient_id: ingredient
            for ingredient_id, ingredient in ingredients.items()
            if ingredient.purchase_mode == "regular"
        }
        blocks_by_day: dict[int, list[cp_model.IntVar]] = {day: [] for day in range(request.days)}
        block_upper_by_day: dict[int, int] = {day: 0 for day in range(request.days)}
        for ingredient_id, ingredient in regular.items():
            increment = int(round(float(ingredient.purchase_increment) * _Q_SCALE))
            price = float(ingredient.price_per_default_unit)
            max_demand = 0
            for _day, _slot, pool in positions:
                max_demand += max(
                    (
                        int(round(item.quantity * _Q_SCALE))
                        for candidate in pool
                        for item in candidate.ingredients
                        if item.ingredient_id == ingredient_id
                    ),
                    default=0,
                )
            max_blocks = max(1, math.ceil(max_demand / increment) + request.days)
            # Keep the real shelf life for end-of-horizon classification.
            # The allocation range is already clipped to the plan horizon;
            # truncating shelf life here incorrectly marks food that expires
            # after the plan as in-horizon waste.
            max_life = ingredient.max_shelf_life_days
            for purchase_day in range(request.days):
                block = model.NewIntVar(0, max_blocks, f"buy_{ingredient_id}_{purchase_day}")
                buy[(ingredient_id, purchase_day)] = block
                blocks_by_day[purchase_day].append(block)
                block_upper_by_day[purchase_day] += max_blocks
                lot_allocations = []
                for use_day in range(purchase_day, min(request.days, purchase_day + max_life + 1)):
                    variable = model.NewIntVar(
                        0, max_demand, f"alloc_{ingredient_id}_{purchase_day}_{use_day}"
                    )
                    allocation[(ingredient_id, purchase_day, use_day)] = variable
                    lot_allocations.append(variable)
                    holding_parts.append(variable * (use_day - purchase_day))
                left = model.NewIntVar(0, increment * max_blocks, f"unused_{ingredient_id}_{purchase_day}")
                unused[(ingredient_id, purchase_day)] = left
                model.Add(sum(lot_allocations) + left == increment * block)
                holding_parts.append(left * (request.days - purchase_day))
                block_price = int(math.ceil(float(ingredient.purchase_increment) * price - 1e-9))
                purchase_parts.append(block_price * block)
                value_coefficient = int(round(price * _VALUE_SCALE / _Q_SCALE))
                if purchase_day + max_life <= request.days - 1:
                    expired_parts.append(value_coefficient * left)
                else:
                    carryover_parts.append(value_coefficient * left)
            inventory_for_ingredient = [
                lot for lot in request.inventory_lots
                if lot.ingredient_id == ingredient_id and lot.unit == ingredient.unit
            ]
            for lot in inventory_for_ingredient:
                fixed_quantity = int(round(lot.quantity * _Q_SCALE))
                lot_allocations = []
                start_day = max(0, lot.available_day - 1)
                end_day = min(request.days - 1, lot.expiry_day - 1)
                for use_day in range(start_day, end_day + 1):
                    variable = model.NewIntVar(
                        0, fixed_quantity, f"inventory_{lot.lot_id}_{use_day}"
                    )
                    inventory_allocation[(lot.lot_id, use_day)] = variable
                    lot_allocations.append(variable)
                left = model.NewIntVar(0, fixed_quantity, f"inventory_unused_{lot.lot_id}")
                inventory_unused[lot.lot_id] = left
                model.Add(sum(lot_allocations) + left == fixed_quantity)
                stock_rotation_parts.append(left * max(1, 1_000 - min(lot.expiry_day, 999)))
                value_coefficient = int(round(lot.cost_basis_per_unit * _VALUE_SCALE / _Q_SCALE))
                if lot.expiry_day <= request.days:
                    expired_parts.append(value_coefficient * left)
                else:
                    carryover_parts.append(value_coefficient * left)
            for use_day in range(request.days):
                sources = [
                    variable
                    for (iid, _purchase_day, day), variable in allocation.items()
                    if iid == ingredient_id and day == use_day
                ]
                sources.extend(
                    variable
                    for (lot_id, day), variable in inventory_allocation.items()
                    if day == use_day and any(
                        lot.lot_id == lot_id and lot.ingredient_id == ingredient_id
                        for lot in inventory_for_ingredient
                    )
                )
                model.Add(sum(sources) == demand[(ingredient_id, use_day)])

        for day, variables in blocks_by_day.items():
            if not variables:
                model.Add(shopping_days[day] == 0)
                continue
            upper = block_upper_by_day[day]
            model.Add(sum(variables) <= upper * shopping_days[day])
            model.Add(sum(variables) >= shopping_days[day])

        purchase_cost = sum(purchase_parts) if purchase_parts else 0
        expired_value = sum(expired_parts) if expired_parts else 0
        carryover_value = sum(carryover_parts) if carryover_parts else 0
        stock_rotation = sum(stock_rotation_parts) if stock_rotation_parts else 0
        holding_quantity_days = sum(holding_parts) if holding_parts else 0
        if request.budget_limit is not None:
            model.Add(purchase_cost <= int(math.floor(request.budget_limit)))

        daily_nutrition: list[dict[str, cp_model.LinearExpr]] = []
        daily_calorie_lower: list[cp_model.LinearExpr] = []
        daily_calorie_upper: list[cp_model.LinearExpr] = []
        daily_protein_lower: list[cp_model.LinearExpr] = []
        nutrition_penalties: list[cp_model.LinearExpr] = []
        for day in range(request.days):
            totals: dict[str, cp_model.LinearExpr] = {}
            for attribute in ("calories", "protein_g", "fat_g", "carb_g"):
                totals[attribute] = sum(
                    int(round(getattr(values[dish_id], attribute) * _N_SCALE)) * variable
                    for (selected_day, _slot, dish_id), variable in x.items()
                    if selected_day == day
                )
            daily_nutrition.append(totals)
            selected_on_day = [
                (values[dish_id], variable)
                for (selected_day, _slot, dish_id), variable in x.items()
                if selected_day == day
            ]
            calorie_lower = sum(
                _scaled_floor(candidate.calories) * variable
                for candidate, variable in selected_on_day
            )
            calorie_upper = sum(
                _scaled_ceil(candidate.calories) * variable
                for candidate, variable in selected_on_day
            )
            protein_lower = sum(
                _scaled_floor(candidate.protein_g) * variable
                for candidate, variable in selected_on_day
            )
            daily_calorie_lower.append(calorie_lower)
            daily_calorie_upper.append(calorie_upper)
            daily_protein_lower.append(protein_lower)
            model.Add(calorie_lower >= _scaled_ceil(request.target_calories, 0.80))
            model.Add(calorie_upper <= _scaled_floor(request.target_calories, 1.20))
            for attribute, target, weight, shortage_only in (
                ("calories", request.target_calories, self._policy.calorie_deviation_weight, False),
                ("protein_g", request.target_protein_g, self._policy.protein_shortage_weight, True),
                ("fat_g", request.target_fat_g, self._policy.macro_deviation_weight, False),
                ("carb_g", request.target_carb_g, self._policy.macro_deviation_weight, False),
            ):
                target_scaled = int(round(target * _N_SCALE))
                difference = model.NewIntVar(-10**7, 10**7, f"diff_{attribute}_{day}")
                model.Add(difference == totals[attribute] - target_scaled)
                penalty = model.NewIntVar(0, 10**7, f"penalty_{attribute}_{day}")
                if shortage_only:
                    model.AddMaxEquality(penalty, [-difference, 0])
                else:
                    model.AddAbsEquality(penalty, difference)
                nutrition_penalties.append(weight * penalty)

        model.Add(
            sum(daily_calorie_lower)
            >= _scaled_ceil(request.target_calories, request.days, 0.90)
        )
        model.Add(
            sum(daily_calorie_upper)
            <= _scaled_floor(request.target_calories, request.days, 1.10)
        )
        model.Add(
            sum(daily_protein_lower)
            >= _scaled_ceil(request.target_protein_g, request.days, 0.90)
        )
        nutrition_score = model.NewIntVar(0, 10**9, "nutrition_score_v3")
        model.Add(nutrition_score == sum(nutrition_penalties))

        self._add_diversity_constraints(model, x, candidates, request, diversity_tier)
        quality_score = self._quality_expression(model, x, candidates, request)
        return _ModelData(
            model=model,
            candidates=candidates,
            ingredients=ingredients,
            x=x,
            buy=buy,
            allocation=allocation,
            unused=unused,
            inventory_allocation=inventory_allocation,
            inventory_unused=inventory_unused,
            shopping_days=shopping_days,
            nutrition_score=nutrition_score,
            purchase_cost=purchase_cost,
            expired_value=expired_value,
            carryover_value=carryover_value,
            stock_rotation=stock_rotation,
            holding_quantity_days=holding_quantity_days,
            quality_score=quality_score,
        )

    def _add_diversity_constraints(
        self,
        model: cp_model.CpModel,
        x: dict[tuple[int, MealType, int], cp_model.IntVar],
        candidates: list[DishCandidate],
        request: PlanRequest,
        tier: str,
    ) -> None:
        if tier == "soft_only":
            return
        base_cap = 1 if request.days <= 3 else 2
        cap = base_cap + (1 if tier == "raised_cap" else 0)
        for candidate in candidates:
            uses = [var for (_day, _slot, dish_id), var in x.items() if dish_id == candidate.dish_id]
            if uses:
                model.Add(sum(uses) <= cap)
            for day in range(request.days):
                lunch = x.get((day, MealType.LUNCH, candidate.dish_id))
                dinner = x.get((day, MealType.DINNER, candidate.dish_id))
                if lunch is not None and dinner is not None:
                    model.Add(lunch + dinner <= 1)
            if tier == "adequate":
                for day in range(1, request.days):
                    for slot in slots_for(request.meals_per_day):
                        previous = x.get((day - 1, slot, candidate.dish_id))
                        current = x.get((day, slot, candidate.dish_id))
                        if previous is not None and current is not None:
                            model.Add(previous + current <= 1)

    def _quality_expression(
        self,
        model: cp_model.CpModel,
        x: dict[tuple[int, MealType, int], cp_model.IntVar],
        candidates: list[DishCandidate],
        request: PlanRequest,
    ) -> cp_model.LinearExpr:
        values = {candidate.dish_id: candidate for candidate in candidates}
        weights = {
            DishType.BREAKFAST: self._policy.breakfast_repeat_penalty,
            DishType.STAPLE: self._policy.staple_repeat_penalty,
            DishType.SAVORY: self._policy.savory_repeat_penalty,
            DishType.VEGETABLE_SIDE: self._policy.side_repeat_penalty,
            DishType.SOUP: self._policy.side_repeat_penalty,
        }
        parts: list[cp_model.LinearExpr] = []
        for candidate in candidates:
            uses = [var for (_day, _slot, dish_id), var in x.items() if dish_id == candidate.dish_id]
            if uses:
                repeat = model.NewIntVar(0, len(uses), f"v3_repeat_{candidate.dish_id}")
                model.AddMaxEquality(repeat, [sum(uses) - 1, 0])
                parts.append(repeat * weights[candidate.dish_type])
        for day in range(request.days):
            for method in {item.cooking_method for item in candidates if item.cooking_method}:
                uses = [
                    variable
                    for (selected_day, _slot, dish_id), variable in x.items()
                    if selected_day == day and values[dish_id].cooking_method == method
                ]
                if uses:
                    repeat = model.NewIntVar(0, len(uses), f"v3_method_{day}_{method.value}")
                    model.AddMaxEquality(repeat, [sum(uses) - 1, 0])
                    parts.append(repeat * self._policy.cooking_method_repeat_penalty)
        preferred = {tag.casefold() for tag in request.preferred_tags}
        for (_day, _slot, dish_id), variable in x.items():
            if preferred.intersection(tag.casefold() for tag in values[dish_id].tags):
                parts.append(-variable * self._policy.preferred_tag_bonus)
        return sum(parts) if parts else 0

    @staticmethod
    def _capture(data: _ModelData, solver: cp_model.CpSolver, status: int) -> _Captured:
        def value(expression: cp_model.LinearExpr) -> int:
            return int(solver.Value(expression)) if not isinstance(expression, int) else expression

        return _Captured(
            x={key: int(solver.Value(variable)) for key, variable in data.x.items()},
            buy={key: int(solver.Value(variable)) for key, variable in data.buy.items()},
            allocation={key: int(solver.Value(variable)) for key, variable in data.allocation.items()},
            unused={key: int(solver.Value(variable)) for key, variable in data.unused.items()},
            inventory_allocation={
                key: int(solver.Value(variable)) for key, variable in data.inventory_allocation.items()
            },
            inventory_unused={
                key: int(solver.Value(variable)) for key, variable in data.inventory_unused.items()
            },
            nutrition_score=int(solver.Value(data.nutrition_score)),
            purchase_cost=value(data.purchase_cost),
            expired_value=value(data.expired_value),
            carryover_value=value(data.carryover_value),
            stock_rotation=value(data.stock_rotation),
            holding_quantity_days=value(data.holding_quantity_days),
            shopping_days=sum(int(solver.Value(variable)) for variable in data.shopping_days.values()),
            status_name=solver.StatusName(status),
        )

    @staticmethod
    def _materialize_days(
        request: PlanRequest,
        candidates: list[DishCandidate],
        _x_vars: dict[tuple[int, MealType, int], cp_model.IntVar],
        x_values: dict[tuple[int, MealType, int], int],
    ) -> list[list[ComposedMeal]]:
        values = {candidate.dish_id: candidate for candidate in candidates}
        result: list[list[ComposedMeal]] = []
        for day in range(request.days):
            meals = []
            for slot in slots_for(request.meals_per_day):
                selected = tuple(
                    values[dish_id]
                    for (selected_day, selected_slot, dish_id), chosen in x_values.items()
                    if selected_day == day and selected_slot == slot and chosen
                )
                meals.append(
                    ComposedMeal(
                        slot=slot,
                        dishes=canonical_dishes_for_meal(ComposedMeal(slot=slot, dishes=selected)),
                    )
                )
            result.append(meals)
        return result

    def _materialize_procurement(
        self,
        request: PlanRequest,
        days: list[list[ComposedMeal]],
        ingredients: dict[int, DishIngredientSnapshot],
    ) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, float]], list[dict[str, float]]]:
        occurrences: dict[int, list[dict[str, Any]]] = {ingredient_id: [] for ingredient_id in ingredients}
        pantry_totals: dict[int, float] = {}
        sequence = 0
        for day_index, meals in enumerate(days):
            for meal in meals:
                for dish in meal.dishes:
                    for ingredient in dish.ingredients:
                        sequence += 1
                        occurrence = {
                            "sequence": sequence,
                            "day": day_index + 1,
                            "day_index": day_index,
                            "slot": meal.slot.value,
                            "dish_id": dish.dish_id,
                            "dish_name": dish.name,
                            "ingredient": ingredient,
                            "base_quantity": ingredient.quantity,
                        }
                        occurrences.setdefault(ingredient.ingredient_id, []).append(occurrence)
                        if ingredient.purchase_mode == "pantry":
                            pantry_totals[ingredient.ingredient_id] = (
                                pantry_totals.get(ingredient.ingredient_id, 0.0) + ingredient.quantity
                            )

        purchase_items, inventory_items = JitProcurementScheduler().schedule(
            request, ingredients, occurrences
        )
        supply_items = inventory_items + purchase_items

        base_nutrition = self._nutrition_by_day(days)
        final_nutrition = [dict(item) for item in base_nutrition]
        adjustments = self._absorb_small_leftovers(
            request, supply_items, occurrences, final_nutrition
        )

        for item in supply_items:
            ingredient = ingredients[item["ingredient_id"]]
            storage_totals: dict[tuple[str, int], float] = {}
            for allocation in item["allocations"]:
                key = (allocation["storage_mode"], allocation["expiry_day"])
                storage_totals[key] = storage_totals.get(key, 0.0) + float(allocation["quantity"])
            remaining = round(float(item["remaining_quantity"]), 2)
            if remaining > 0:
                if item["source_kind"] == "inventory":
                    mode = item["_fixed_storage_mode"]
                    expiry = item["_fixed_expiry_day"]
                else:
                    mode, expiry = self._longest_storage(ingredient, int(item["purchase_day"]))
                storage_totals[(mode, expiry)] = storage_totals.get((mode, expiry), 0.0) + remaining
                if expiry <= request.days:
                    item["expired_waste_quantity"] = remaining
                else:
                    item["carryover_quantity"] = remaining
            item["storage_splits"] = [
                {"mode": mode, "quantity": round(quantity, 2), "expiry_day": expiry}
                for (mode, expiry), quantity in sorted(storage_totals.items())
            ]
            item["required_quantity"] = round(
                sum(float(allocation["quantity"]) for allocation in item["allocations"]), 2
            )
            for allocation in item["allocations"]:
                allocation.pop("sequence", None)

        pantry_checks = [
            {
                "item_key": f"pantry:{ingredient_id}",
                "ingredient_id": ingredient_id,
                "name": ingredients[ingredient_id].name,
                "quantity": round(quantity, 2),
                "unit": ingredients[ingredient_id].unit,
            }
            for ingredient_id, quantity in sorted(pantry_totals.items())
        ]
        purchase_cost = sum(float(item["purchase_cost"]) for item in purchase_items)
        purchase_consumption_value = sum(
            float(allocation["quantity"]) * float(item["price_per_default_unit"])
            for item in purchase_items for allocation in item["allocations"]
        )
        inventory_consumption_value = sum(
            float(allocation["quantity"]) * float(item["price_per_default_unit"])
            for item in inventory_items for allocation in item["allocations"]
        )
        expired_value = sum(
            float(item["expired_waste_quantity"]) * float(item["price_per_default_unit"])
            for item in supply_items
        )
        carryover_value = sum(
            float(item["carryover_quantity"]) * float(item["price_per_default_unit"])
            for item in supply_items
        )
        procurement = {
            "purchase_items": purchase_items,
            "inventory_items": inventory_items,
            "pantry_checks": pantry_checks,
            "cost_summary": {
                "purchase_cost": round(purchase_cost),
                "consumption_value": round(
                    purchase_consumption_value + inventory_consumption_value
                ),
                "purchase_consumption_value": round(purchase_consumption_value),
                "inventory_consumption_value": round(inventory_consumption_value),
                "expired_waste_value": round(expired_value),
                "ending_carryover_value": round(carryover_value),
            },
            "shopping_days": sorted({item["purchase_day"] for item in purchase_items}),
        }
        procurement["ledger_version"] = 2
        procurement["daily_ledger"] = build_daily_ledger(request, supply_items)
        for item in supply_items:
            for key in tuple(item):
                if key.startswith("_"):
                    item.pop(key, None)
        return procurement, adjustments, base_nutrition, final_nutrition

    def _absorb_small_leftovers(
        self,
        request: PlanRequest,
        purchase_items: list[dict[str, Any]],
        occurrences: dict[int, list[dict[str, Any]]],
        daily_nutrition: list[dict[str, float]],
    ) -> list[dict[str, Any]]:
        adjustments: list[dict[str, Any]] = []
        current_score = self._nutrition_score(daily_nutrition, request)
        for item in sorted(purchase_items, key=lambda value: (value["purchase_day"], value["ingredient_id"])):
            remainder = float(item["remaining_quantity"])
            increment = float(item["purchase_increment"])
            if remainder <= 1e-8 or remainder > increment * 0.20 + 1e-8:
                continue
            allocations = item["allocations"]
            if not allocations:
                continue
            first_sequence = min(int(allocation["sequence"]) for allocation in allocations)
            ingredient_id = int(item["ingredient_id"])
            for occurrence in occurrences.get(ingredient_id, []):
                if remainder <= 1e-8 or int(occurrence["sequence"]) <= first_sequence:
                    continue
                ingredient: DishIngredientSnapshot = occurrence["ingredient"]
                if item["source_kind"] == "inventory":
                    if int(occurrence["day"]) > int(item["_fixed_expiry_day"]):
                        continue
                elif int(occurrence["day"]) - int(item["purchase_day"]) > ingredient.max_shelf_life_days:
                    continue
                step = ingredient.extra_step_quantity
                if ingredient.max_extra_quantity <= 0 or step is None or step > remainder + 1e-8:
                    continue
                max_steps = min(
                    math.floor(ingredient.max_extra_quantity / step),
                    math.floor((remainder + 1e-8) / step),
                )
                accepted = 0.0
                for _ in range(max_steps):
                    delta = ingredient.nutrition_for(step)
                    day_index = int(occurrence["day_index"])
                    if daily_nutrition[day_index]["calories"] + delta["calories"] > request.target_calories + 1e-6:
                        break
                    trial = [dict(value) for value in daily_nutrition]
                    for key, value in delta.items():
                        trial[day_index][key] += value
                    score = self._nutrition_score(trial, request)
                    if score > current_score:
                        break
                    daily_nutrition[:] = trial
                    current_score = score
                    accepted += step
                    remainder -= step
                if accepted <= 0:
                    continue
                delta = ingredient.nutrition_for(accepted)
                item["remaining_quantity"] = round(remainder, 2)
                if item["source_kind"] == "inventory":
                    mode = item["_fixed_storage_mode"]
                    expiry = item["_fixed_expiry_day"]
                else:
                    mode, expiry = self._storage_for(
                        ingredient,
                        int(occurrence["day"]) - int(item["purchase_day"]),
                        int(item["purchase_day"]),
                    )
                item["allocations"].append({
                    "day": occurrence["day"],
                    "slot": occurrence["slot"],
                    "dish_id": occurrence["dish_id"],
                    "dish_name": occurrence["dish_name"],
                    "quantity": round(accepted, 2),
                    "kind": "extra",
                    "storage_mode": mode,
                    "expiry_day": expiry,
                    "sequence": occurrence["sequence"],
                })
                adjustments.append({
                    "day": occurrence["day"],
                    "slot": occurrence["slot"],
                    "dish_id": occurrence["dish_id"],
                    "ingredient_id": ingredient_id,
                    "base_quantity": ingredient.quantity,
                    "extra_quantity": round(accepted, 2),
                    "actual_quantity": round(ingredient.quantity + accepted, 2),
                    "unit": ingredient.unit,
                    "purchase_day": item["purchase_day"],
                    "reason": "leftover_absorption",
                    "nutrition_delta": {key: round(value, 2) for key, value in delta.items()},
                })
        return adjustments

    @staticmethod
    def _storage_for(
        ingredient: DishIngredientSnapshot, delta_days: int, purchase_day: int
    ) -> tuple[str, int]:
        options = (
            ("room", ingredient.room_shelf_life_days),
            ("fridge", ingredient.fridge_shelf_life_days),
            ("freezer", ingredient.freezer_shelf_life_days),
        )
        for mode, shelf_life in options:
            if shelf_life is not None and shelf_life >= delta_days:
                return mode, purchase_day + shelf_life
        if delta_days == 0:
            return "same_day", purchase_day
        raise ValueError(f"Không có phương thức bảo quản hợp lệ cho {ingredient.name}")

    @staticmethod
    def _longest_storage(
        ingredient: DishIngredientSnapshot, purchase_day: int
    ) -> tuple[str, int]:
        options = [
            ("room", ingredient.room_shelf_life_days),
            ("fridge", ingredient.fridge_shelf_life_days),
            ("freezer", ingredient.freezer_shelf_life_days),
        ]
        available = [(mode, value) for mode, value in options if value is not None]
        if not available:
            return "same_day", purchase_day
        mode, shelf_life = max(available, key=lambda item: item[1])
        return mode, purchase_day + int(shelf_life)

    @staticmethod
    def _nutrition_by_day(days: list[list[ComposedMeal]]) -> list[dict[str, float]]:
        return [
            {
                "calories": sum(meal.calories for meal in day),
                "protein_g": sum(meal.protein_g for meal in day),
                "fat_g": sum(meal.fat_g for meal in day),
                "carb_g": sum(meal.carb_g for meal in day),
            }
            for day in days
        ]

    def _nutrition_score(
        self, daily: list[dict[str, float]], request: PlanRequest
    ) -> int:
        score = 0
        for totals in daily:
            for key, target, weight, shortage_only in (
                ("calories", request.target_calories, self._policy.calorie_deviation_weight, False),
                ("protein_g", request.target_protein_g, self._policy.protein_shortage_weight, True),
                ("fat_g", request.target_fat_g, self._policy.macro_deviation_weight, False),
                ("carb_g", request.target_carb_g, self._policy.macro_deviation_weight, False),
            ):
                difference = int(round((totals[key] - target) * _N_SCALE))
                penalty = max(0, -difference) if shortage_only else abs(difference)
                score += penalty * weight
        return score

    @staticmethod
    def source_fingerprint(request: PlanRequest, days: list[list[ComposedMeal]]) -> str:
        return source_fingerprint(request, days)

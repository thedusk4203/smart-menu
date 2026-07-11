"""CP-SAT optimizer cho Dish Planner V2.

Mọi tổng đều scale sang integer trước khi đưa vào OR-Tools; không có logic
greedy nào quyết định một bữa độc lập với ngân sách/nutrition còn lại.
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass

from ortools.sat.python import cp_model

from app.modules.meal_planning.composition import canonical_dishes_for_meal, slots_for
from app.modules.meal_planning.domain import ComposedMeal, DishCandidate, PlanRequest, QualityPolicy
from app.modules.meal_planning.quality import DEFAULT_QUALITY_POLICY
from app.shared.enums import DishType, MealType


_NUTRITION_SCALE = 10


@dataclass(frozen=True)
class OptimizationResult:
    days: list[list[ComposedMeal]]
    nutrition_score: int
    solver_time_ms: int
    solver_status: str
    timed_out_with_solution: bool = False


class DishCpSatOptimizer:
    def __init__(self, policy: QualityPolicy = DEFAULT_QUALITY_POLICY) -> None:
        self._policy = policy

    def solve(
        self,
        request: PlanRequest,
        candidates: list[DishCandidate],
        *,
        seed: int | None = None,
    ) -> OptimizationResult | None:
        started = time.perf_counter()
        candidates = sorted(candidates, key=lambda candidate: candidate.dish_id)
        # Luôn lấy một nghiệm hard-constraint trước. Đây là hàng rào chống
        # false-infeasible khi CP-SAT cần thêm thời gian để tối ưu objective.
        feasibility_model, feasibility_x, _, _ = self._build_model(
            request, candidates, include_nutrition=False, include_quality=False
        )
        self._add_regenerate_difference(feasibility_model, feasibility_x, request.previous_plan_signature)
        self._add_nutrition_hint(feasibility_model, feasibility_x, candidates, request)
        # 20 ms không đủ ổn định khi test/process vừa khởi động hoặc CPU đang
        # bận: CP-SAT có thể trả UNKNOWN trước khi nhận hint làm incumbent và
        # planner biến một bài toán hợp lệ thành infeasible. 50 ms vẫn giữ tổng
        # time budget dưới ngưỡng web latency, nhưng đủ cho pha hard-constraint
        # xác nhận có nghiệm.
        feasibility_solver = self._solver(
            seed, 0.05, fix_hint=not bool(request.previous_plan_signature)
        )
        feasibility_status = feasibility_solver.Solve(feasibility_model)
        if feasibility_status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return None
        fallback_days = self._materialize(request, candidates, feasibility_x, feasibility_solver)
        fallback_nutrition = self._nutrition_score_from_days(fallback_days, request)

        nutrition_model, nutrition_x, nutrition_score, _ = self._build_model(
            request, candidates, include_nutrition=True, include_quality=False
        )
        self._add_regenerate_difference(nutrition_model, nutrition_x, request.previous_plan_signature)
        self._add_nutrition_hint(nutrition_model, nutrition_x, candidates, request)
        # Instance nhỏ có thể tìm optimum thật trong vài trăm ms; với instance
        # benchmark lớn ưu tiên luôn trả feasible plan dưới ngưỡng web latency.
        nutrition_timeout = 0.30 if request.days * len(candidates) <= 100 else max(
            self._policy.timeout_seconds - 0.18, 0.12
        )
        nutrition_solver = self._solver(seed, nutrition_timeout)
        nutrition_model.Minimize(nutrition_score)
        nutrition_status = nutrition_solver.Solve(nutrition_model)
        if nutrition_status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            selected_solver = nutrition_solver
            selected_x = nutrition_x
            selected_nutrition = nutrition_score
            selected_status = nutrition_status
            best_nutrition = int(nutrition_solver.Value(nutrition_score))
            selected_nutrition_score = best_nutrition
        else:
            selected_solver = feasibility_solver
            selected_x = feasibility_x
            selected_nutrition = None
            selected_nutrition_score = fallback_nutrition
            selected_status = feasibility_status
            best_nutrition = fallback_nutrition

        second_status = cp_model.UNKNOWN
        # Không dựng model đa dạng nặng khi phase nutrition chưa có incumbent.
        # Lúc đó fallback đã hợp lệ và warning timeout minh bạch hơn giả infeasible.
        if nutrition_status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            slack = math.ceil(best_nutrition * self._policy.regenerate_quality_slack_pct / 100)
            limit = best_nutrition + (slack if request.previous_plan_signature else 0)
            second_model, second_x, second_nutrition, quality_score = self._build_model(
                request, candidates, include_nutrition=True, include_quality=True
            )
            self._add_regenerate_difference(second_model, second_x, request.previous_plan_signature)
            second_model.Add(second_nutrition <= limit)
            second_model.Minimize(quality_score)
            second = self._solver(seed, 0.07)
            second_status = second.Solve(second_model)
            if second_status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
                selected_solver = second
                selected_x = second_x
                selected_nutrition = second_nutrition
                selected_nutrition_score = int(second.Value(second_nutrition))
                selected_status = second_status
        days = self._materialize(request, candidates, selected_x, selected_solver)
        elapsed = int((time.perf_counter() - started) * 1000)
        return OptimizationResult(
            days=days,
            nutrition_score=selected_nutrition_score,
            solver_time_ms=elapsed,
            solver_status=selected_solver.StatusName(selected_status),
            timed_out_with_solution=(
                nutrition_status not in (cp_model.OPTIMAL, cp_model.FEASIBLE)
                or second_status not in (cp_model.OPTIMAL, cp_model.FEASIBLE)
                or selected_status == cp_model.FEASIBLE
            ),
        )

    def _solver(
        self, seed: int | None, timeout_seconds: float, *, fix_hint: bool = False
    ) -> cp_model.CpSolver:
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = timeout_seconds
        solver.parameters.num_search_workers = 1
        solver.parameters.random_seed = 0 if seed is None else seed
        solver.parameters.use_optimization_hints = True
        solver.parameters.fix_variables_to_their_hinted_value = fix_hint
        return solver

    def _build_model(
        self,
        request: PlanRequest,
        candidates: list[DishCandidate],
        *,
        include_nutrition: bool,
        include_quality: bool,
    ) -> tuple[cp_model.CpModel, dict[tuple[int, MealType, int], cp_model.IntVar], cp_model.IntVar, cp_model.LinearExpr]:
        model = cp_model.CpModel()
        pools: dict[DishType, list[DishCandidate]] = {dish_type: [] for dish_type in DishType}
        for candidate in candidates:
            pools[candidate.dish_type].append(candidate)
        side_pool = pools[DishType.VEGETABLE_SIDE] + pools[DishType.SOUP]
        positions: list[tuple[int, MealType, list[DishCandidate]]] = []
        for day in range(request.days):
            for slot in slots_for(request.meals_per_day):
                if slot == MealType.BREAKFAST:
                    positions.append((day, slot, pools[DishType.BREAKFAST]))
                else:
                    positions.extend(
                        [
                            (day, slot, pools[DishType.STAPLE]),
                            (day, slot, pools[DishType.SAVORY]),
                            (day, slot, side_pool),
                        ]
                    )
        x: dict[tuple[int, MealType, int], cp_model.IntVar] = {}
        for day, slot, pool in positions:
            variables: list[cp_model.IntVar] = []
            for candidate in pool:
                key = (day, slot, candidate.dish_id)
                variable = x.get(key)
                if variable is None:
                    variable = model.NewBoolVar(f"x_{day}_{slot.value}_{candidate.dish_id}")
                    x[key] = variable
                variables.append(variable)
            model.AddExactlyOne(variables)

        if request.budget_limit is not None:
            model.Add(
                sum(
                    int(round(candidate.estimated_cost)) * variable
                    for (day, slot, dish_id), variable in x.items()
                    for candidate in [self._candidate(candidates, dish_id)]
                )
                <= int(math.floor(request.budget_limit))
            )

        nutrition_score = None
        if include_nutrition:
            nutrition_parts: list[cp_model.IntVar] = []
            for day in range(request.days):
                selected = [(dish_id, variable) for (d, _slot, dish_id), variable in x.items() if d == day]
                nutrition_parts.extend(
                    self._daily_nutrition_penalties(model, candidates, selected, request, day)
                )
            nutrition_score = model.NewIntVar(0, 10**9, "nutrition_score")
            model.Add(nutrition_score == sum(nutrition_parts))

        quality_score = None
        if include_quality:
            quality_parts = self._quality_penalties(model, candidates, x, request)
            # Một số hạng có thể âm (tag ưu tiên), vì vậy không dùng lower bound 0.
            quality_score = sum(quality_parts) if quality_parts else 0
        return model, x, nutrition_score, quality_score

    @staticmethod
    def _candidate(candidates: list[DishCandidate], dish_id: int) -> DishCandidate:
        # danh sách nhỏ và chỉ gọi khi dựng model; tránh state mutable trên optimizer.
        return next(candidate for candidate in candidates if candidate.dish_id == dish_id)

    def _daily_nutrition_penalties(
        self,
        model: cp_model.CpModel,
        candidates: list[DishCandidate],
        selected: list[tuple[int, cp_model.IntVar]],
        request: PlanRequest,
        day: int,
    ) -> list[cp_model.IntVar]:
        values = {candidate.dish_id: candidate for candidate in candidates}
        parts: list[cp_model.IntVar] = []
        config = (
            ("calories", request.target_calories, self._policy.calorie_deviation_weight, False),
            ("protein_g", request.target_protein_g, self._policy.protein_shortage_weight, True),
            ("fat_g", request.target_fat_g, self._policy.macro_deviation_weight, False),
            ("carb_g", request.target_carb_g, self._policy.macro_deviation_weight, False),
        )
        for attribute, target, weight, shortage_only in config:
            target_value = int(round(target * _NUTRITION_SCALE))
            total = sum(
                int(round(getattr(values[dish_id], attribute) * _NUTRITION_SCALE)) * variable
                for dish_id, variable in selected
            )
            if shortage_only:
                penalty = model.NewIntVar(0, max(target_value, 1), f"short_{attribute}_{day}")
                model.AddMaxEquality(penalty, [target_value - total, 0])
            else:
                penalty = model.NewIntVar(0, 1_000_000, f"dev_{attribute}_{day}")
                model.AddAbsEquality(penalty, total - target_value)
            weighted = model.NewIntVar(0, 1_000_000_000, f"weighted_{attribute}_{day}")
            model.Add(weighted == penalty * weight)
            parts.append(weighted)
        return parts

    def _add_nutrition_hint(
        self,
        model: cp_model.CpModel,
        x: dict[tuple[int, MealType, int], cp_model.IntVar],
        candidates: list[DishCandidate],
        request: PlanRequest,
    ) -> None:
        """Cung cấp incumbent hợp lệ giàu dinh dưỡng để CP-SAT không phải bắt
        đầu từ assignment ngẫu nhiên ở instance 7 ngày lớn.

        Hint không thay thế solver, không nới hard constraint và có thể bị solver
        thay đổi. Khi budget không đủ hint nutrition, dùng tổ hợp rẻ nhất.
        """
        pools: dict[DishType, list[DishCandidate]] = {dish_type: [] for dish_type in DishType}
        for candidate in candidates:
            pools[candidate.dish_type].append(candidate)
        side = pools[DishType.VEGETABLE_SIDE] + pools[DishType.SOUP]

        def score(dishes: tuple[DishCandidate, ...], divisor: float) -> float:
            calories = sum(dish.calories for dish in dishes)
            protein = sum(dish.protein_g for dish in dishes)
            fat = sum(dish.fat_g for dish in dishes)
            carb = sum(dish.carb_g for dish in dishes)
            return (
                abs(calories - request.target_calories / divisor) * self._policy.calorie_deviation_weight
                + max(0, request.target_protein_g / divisor - protein) * self._policy.protein_shortage_weight
                + abs(fat - request.target_fat_g / divisor) * self._policy.macro_deviation_weight
                + abs(carb - request.target_carb_g / divisor) * self._policy.macro_deviation_weight
            )

        if request.meals_per_day == 3:
            breakfast = min(pools[DishType.BREAKFAST], key=lambda dish: score((dish,), 3))
        else:
            breakfast = None
        main_options = [
            (staple, savory, side_dish)
            for staple in pools[DishType.STAPLE]
            for savory in pools[DishType.SAVORY]
            for side_dish in side
        ]
        main = min(main_options, key=lambda dishes: score(dishes, 3 if request.meals_per_day == 3 else 2))
        selected_ids = {dish.dish_id for dish in main}
        if breakfast:
            selected_ids.add(breakfast.dish_id)
        one_day_cost = sum(dish.estimated_cost for dish in main) * 2 + (breakfast.estimated_cost if breakfast else 0)
        if request.budget_limit is not None and one_day_cost * request.days > request.budget_limit:
            cheapest_main = (
                min(pools[DishType.STAPLE], key=lambda dish: dish.estimated_cost),
                min(pools[DishType.SAVORY], key=lambda dish: dish.estimated_cost),
                min(side, key=lambda dish: dish.estimated_cost),
            )
            selected_ids = {dish.dish_id for dish in cheapest_main}
            if breakfast:
                selected_ids.add(min(pools[DishType.BREAKFAST], key=lambda dish: dish.estimated_cost).dish_id)
        for key, variable in x.items():
            model.AddHint(variable, 1 if key[2] in selected_ids else 0)

    def _nutrition_score_from_days(
        self, days: list[list[ComposedMeal]], request: PlanRequest
    ) -> int:
        """Cùng công thức objective với model, dùng khi timeout ở pha tối ưu."""
        score = 0
        for day in days:
            totals = {
                attribute: sum(
                    int(round(getattr(dish, attribute) * _NUTRITION_SCALE))
                    for meal in day for dish in meal.dishes
                )
                for attribute in ("calories", "protein_g", "fat_g", "carb_g")
            }
            for attribute, target, weight, shortage_only in (
                ("calories", request.target_calories, self._policy.calorie_deviation_weight, False),
                ("protein_g", request.target_protein_g, self._policy.protein_shortage_weight, True),
                ("fat_g", request.target_fat_g, self._policy.macro_deviation_weight, False),
                ("carb_g", request.target_carb_g, self._policy.macro_deviation_weight, False),
            ):
                difference = totals[attribute] - int(round(target * _NUTRITION_SCALE))
                penalty = max(0, -difference) if shortage_only else abs(difference)
                score += penalty * weight
        return score

    def _quality_penalties(
        self,
        model: cp_model.CpModel,
        candidates: list[DishCandidate],
        x: dict[tuple[int, MealType, int], cp_model.IntVar],
        request: PlanRequest,
    ) -> list[cp_model.LinearExpr]:
        values = {candidate.dish_id: candidate for candidate in candidates}
        parts: list[cp_model.LinearExpr] = []
        weights = {
            DishType.SAVORY: self._policy.savory_repeat_penalty,
            DishType.VEGETABLE_SIDE: self._policy.side_repeat_penalty,
            DishType.SOUP: self._policy.side_repeat_penalty,
            DishType.BREAKFAST: self._policy.breakfast_repeat_penalty,
            DishType.STAPLE: self._policy.staple_repeat_penalty,
        }
        for candidate in candidates:
            uses = [var for (_day, _slot, dish_id), var in x.items() if dish_id == candidate.dish_id]
            if not uses:
                continue
            repeat = model.NewIntVar(0, len(uses), f"repeat_{candidate.dish_id}")
            model.AddMaxEquality(repeat, [sum(uses) - 1, 0])
            parts.append(repeat * weights[candidate.dish_type])

            for day in range(request.days):
                lunch = x.get((day, MealType.LUNCH, candidate.dish_id))
                dinner = x.get((day, MealType.DINNER, candidate.dish_id))
                if lunch is not None and dinner is not None:
                    same_day = model.NewBoolVar(f"same_day_{day}_{candidate.dish_id}")
                    model.Add(same_day >= lunch + dinner - 1)
                    parts.append(same_day * self._policy.same_day_repeat_penalty)
            for day in range(1, request.days):
                for slot in slots_for(request.meals_per_day):
                    previous = x.get((day - 1, slot, candidate.dish_id))
                    current = x.get((day, slot, candidate.dish_id))
                    if previous is not None and current is not None:
                        consecutive = model.NewBoolVar(f"consecutive_{day}_{slot.value}_{candidate.dish_id}")
                        model.Add(consecutive >= previous + current - 1)
                        parts.append(consecutive * self._policy.consecutive_repeat_penalty)

        for day in range(request.days):
            for method in {candidate.cooking_method for candidate in candidates if candidate.cooking_method}:
                uses = [
                    var for (_d, _slot, dish_id), var in x.items()
                    if _d == day and values[dish_id].cooking_method == method
                ]
                if uses:
                    repeat = model.NewIntVar(0, len(uses), f"method_repeat_{day}_{method.value}")
                    model.AddMaxEquality(repeat, [sum(uses) - 1, 0])
                    parts.append(repeat * self._policy.cooking_method_repeat_penalty)

        preferred = {tag.casefold() for tag in request.preferred_tags}
        for (_day, _slot, dish_id), variable in x.items():
            candidate = values[dish_id]
            if preferred.intersection(tag.casefold() for tag in candidate.tags):
                parts.append(-variable * self._policy.preferred_tag_bonus)
            parts.append(variable * int(round(candidate.estimated_cost)) * self._policy.cost_weight)
        return parts

    def _add_regenerate_difference(
        self,
        model: cp_model.CpModel,
        x: dict[tuple[int, MealType, int], cp_model.IntVar],
        signature: str | None,
    ) -> None:
        if not signature:
            return
        old = []
        for item in signature.split("|"):
            try:
                day, slot, dish_id = item.split(":")
                key = (int(day), MealType(slot), int(dish_id))
            except (TypeError, ValueError):
                continue
            if key in x:
                old.append(x[key])
        if old:
            model.Add(sum(old) <= len(old) - 1)

    def _materialize(
        self,
        request: PlanRequest,
        candidates: list[DishCandidate],
        x: dict[tuple[int, MealType, int], cp_model.IntVar],
        solver: cp_model.CpSolver,
    ) -> list[list[ComposedMeal]]:
        values = {candidate.dish_id: candidate for candidate in candidates}
        days: list[list[ComposedMeal]] = []
        for day in range(request.days):
            meals: list[ComposedMeal] = []
            for slot in slots_for(request.meals_per_day):
                selected = tuple(
                    values[dish_id]
                    for (selected_day, selected_slot, dish_id), variable in x.items()
                    if selected_day == day and selected_slot == slot and solver.Value(variable)
                )
                meals.append(ComposedMeal(slot=slot, dishes=canonical_dishes_for_meal(ComposedMeal(slot, selected))))
            days.append(meals)
        return days

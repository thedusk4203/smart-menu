"""CP-SAT optimizer cho Dish Planner V2.

Mọi tổng đều scale sang integer trước khi đưa vào OR-Tools; không có logic
greedy nào quyết định một bữa độc lập với ngân sách/nutrition còn lại.
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass
from itertools import product

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
        candidates = self._shortlist_candidates(request, candidates)
        hint_selection = self._build_diverse_hint(request, candidates, seed=seed)
        # Luôn lấy một nghiệm hard-constraint trước. Đây là hàng rào chống
        # false-infeasible khi CP-SAT cần thêm thời gian để tối ưu objective.
        feasibility_model, feasibility_x, _, _ = self._build_model(
            request, candidates, include_nutrition=False, include_quality=False
        )
        self._add_regenerate_difference(feasibility_model, feasibility_x, request.previous_plan_signature)
        self._add_selection_hint(feasibility_model, feasibility_x, hint_selection)
        # 20 ms không đủ ổn định khi test/process vừa khởi động hoặc CPU đang
        # bận: CP-SAT có thể trả UNKNOWN trước khi nhận hint làm incumbent và
        # planner biến một bài toán hợp lệ thành infeasible. 50 ms vẫn giữ tổng
        # time budget dưới ngưỡng web latency, nhưng đủ cho pha hard-constraint
        # xác nhận có nghiệm.
        feasibility_solver = self._solver(
            seed,
            0.05,
            fix_hint=self._hint_satisfies_regenerate_constraint(
                hint_selection, request.previous_plan_signature
            ),
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
        self._add_selection_hint(nutrition_model, nutrition_x, hint_selection)
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
            # The nutrition optimum can be a very narrow corner of the search
            # space (and often repeats the same cheap dish).  Keep nutrition
            # close to that optimum, then let the next phase choose the most
            # varied plan inside the tolerance for every generation, not only
            # when the user explicitly asks to regenerate.
            slack = math.ceil(best_nutrition * self._policy.quality_nutrition_slack_pct / 100)
            limit = best_nutrition + slack
            second_model, second_x, second_nutrition, quality_score = self._build_model(
                request, candidates, include_nutrition=True, include_quality=True
            )
            self._add_regenerate_difference(second_model, second_x, request.previous_plan_signature)
            self._add_selection_hint(second_model, second_x, hint_selection)
            second_model.Add(second_nutrition <= limit)
            second_model.Minimize(quality_score)
            second = self._solver(seed, 0.12)
            second_status = second.Solve(second_model)
            if second_status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
                selected_solver = second
                selected_x = second_x
                selected_nutrition = second_nutrition
                selected_nutrition_score = int(second.Value(second_nutrition))
                selected_status = second_status
            elif fallback_nutrition <= limit:
                # The constructive hint is already inside the accepted
                # nutrition band.  Keep its diversity when the heavier quality
                # model times out instead of exposing the repetitive nutrition
                # optimum to the user.
                selected_solver = feasibility_solver
                selected_x = feasibility_x
                selected_nutrition = None
                selected_nutrition_score = fallback_nutrition
                selected_status = feasibility_status
        days = self._materialize(request, candidates, selected_x, selected_solver)
        if self._diversity_score_from_days(fallback_days) < self._diversity_score_from_days(days):
            days = fallback_days
            selected_solver = feasibility_solver
            selected_nutrition_score = fallback_nutrition
            selected_status = feasibility_status
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

    def _shortlist_candidates(
        self, request: PlanRequest, candidates: list[DishCandidate]
    ) -> list[DishCandidate]:
        """Bound CP-SAT and Cartesian-product size as the catalog grows.

        A catalog with 45 staples, 250 savory dishes and 215 sides creates more
        than 2.4 million main-meal combinations.  The planner only needs enough
        strong alternatives to fill the requested slots without repetition.
        Each shortlist keeps the cheapest candidates (budget feasibility), the
        best nutrition matches, preferred tags and cooking-method variety.
        """
        preferred = {tag.casefold() for tag in request.preferred_tags}
        main_uses = request.days * 2
        groups = (
            ({DishType.BREAKFAST}, request.days),
            ({DishType.STAPLE}, main_uses),
            ({DishType.SAVORY}, main_uses),
            ({DishType.VEGETABLE_SIDE, DishType.SOUP}, main_uses),
        )
        shortlisted: list[DishCandidate] = []

        for dish_types, required_uses in groups:
            pool = [candidate for candidate in candidates if candidate.dish_type in dish_types]
            cap = min(len(pool), max(10, required_uses + 4))
            if len(pool) <= cap:
                shortlisted.extend(pool)
                continue

            nutrition_ranked = sorted(
                pool,
                key=lambda candidate: (
                    self._meal_nutrition_score(request, (candidate,)),
                    candidate.dish_id,
                ),
            )
            cheapest = sorted(pool, key=lambda candidate: (candidate.estimated_cost, candidate.dish_id))
            tagged = [
                candidate for candidate in nutrition_ranked
                if preferred.intersection(tag.casefold() for tag in candidate.tags)
            ]
            best_by_method: list[DishCandidate] = []
            seen_methods = set()
            for candidate in nutrition_ranked:
                if candidate.cooking_method is not None and candidate.cooking_method not in seen_methods:
                    seen_methods.add(candidate.cooking_method)
                    best_by_method.append(candidate)

            chosen: dict[int, DishCandidate] = {}

            def add(sequence: list[DishCandidate], limit: int) -> None:
                added = 0
                for candidate in sequence:
                    if candidate.dish_id in chosen:
                        continue
                    chosen[candidate.dish_id] = candidate
                    added += 1
                    if len(chosen) >= cap or added >= limit:
                        break

            add(cheapest, max(2, cap // 4))
            add(tagged, max(2, cap // 4))
            add(best_by_method, cap)
            add(nutrition_ranked, cap)
            shortlisted.extend(chosen.values())

        return sorted(shortlisted, key=lambda candidate: candidate.dish_id)

    def _meal_nutrition_score(
        self, request: PlanRequest, dishes: tuple[DishCandidate, ...]
    ) -> float:
        divisor = float(request.meals_per_day)
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

    @staticmethod
    def _add_selection_hint(
        model: cp_model.CpModel,
        x: dict[tuple[int, MealType, int], cp_model.IntVar],
        selection: dict[tuple[int, MealType], set[int]],
    ) -> None:
        for (day, slot, dish_id), variable in x.items():
            model.AddHint(variable, int(dish_id in selection[(day, slot)]))

    def _build_diverse_hint(
        self,
        request: PlanRequest,
        candidates: list[DishCandidate],
        *,
        seed: int | None,
    ) -> dict[tuple[int, MealType], set[int]]:
        """Build a valid, budget-aware incumbent that is diverse by default.

        Large real-world pools can spend the entire CP-SAT time budget in
        presolve.  The old hint repeated one nutritionally convenient meal in
        every slot, so a timeout exposed that repetition to users.  This hint
        stays near the best per-meal nutrition band, then lexicographically
        avoids same-day, consecutive and global repeats.  CP-SAT may still
        improve it; if it times out, the fallback remains useful.
        """
        pools: dict[DishType, list[DishCandidate]] = {dish_type: [] for dish_type in DishType}
        for candidate in candidates:
            pools[candidate.dish_type].append(candidate)
        side_pool = pools[DishType.VEGETABLE_SIDE] + pools[DishType.SOUP]

        breakfast_options = [(dish,) for dish in pools[DishType.BREAKFAST]]
        main_options = list(product(pools[DishType.STAPLE], pools[DishType.SAVORY], side_pool))
        positions: list[tuple[int, MealType, list[tuple[DishCandidate, ...]]]] = []
        for day in range(request.days):
            for slot in slots_for(request.meals_per_day):
                positions.append((day, slot, breakfast_options if slot == MealType.BREAKFAST else main_options))

        minimum_remaining_cost = [0.0] * (len(positions) + 1)
        for index in range(len(positions) - 1, -1, -1):
            cheapest = min(sum(dish.estimated_cost for dish in option) for option in positions[index][2])
            minimum_remaining_cost[index] = minimum_remaining_cost[index + 1] + cheapest

        selected: dict[tuple[int, MealType], set[int]] = {}
        usage_count: dict[int, int] = {}
        day_ids: dict[int, set[int]] = {}
        day_methods: dict[int, set] = {}
        spent = 0.0
        seed_value = 0 if seed is None else seed
        previous_selection: dict[tuple[int, MealType], set[int]] = {}
        if request.previous_plan_signature:
            for item in request.previous_plan_signature.split("|"):
                try:
                    previous_day, previous_slot, previous_dish_id = item.split(":")
                    previous_selection.setdefault(
                        (int(previous_day) - 1, MealType(previous_slot)), set()
                    ).add(int(previous_dish_id))
                except (TypeError, ValueError):
                    continue
        differs_from_previous = False
        repeat_weights = {
            DishType.BREAKFAST: self._policy.breakfast_repeat_penalty,
            DishType.STAPLE: self._policy.staple_repeat_penalty,
            DishType.SAVORY: self._policy.savory_repeat_penalty,
            DishType.VEGETABLE_SIDE: self._policy.side_repeat_penalty,
            DishType.SOUP: self._policy.side_repeat_penalty,
        }

        for index, (day, slot, options) in enumerate(positions):
            affordable = [
                option
                for option in options
                if request.budget_limit is None
                or spent + sum(dish.estimated_cost for dish in option) + minimum_remaining_cost[index + 1]
                <= request.budget_limit + 1e-6
            ]
            # Precheck guarantees a feasible budget, but retaining this guard
            # keeps the hint builder safe when used independently in tests.
            choices = affordable or options

            today = day_ids.setdefault(day, set())
            minimum_same_day = min(sum(dish.dish_id in today for dish in option) for option in choices)
            choices = [
                option for option in choices
                if sum(dish.dish_id in today for dish in option) == minimum_same_day
            ]

            previous = selected.get((day - 1, slot), set())
            minimum_consecutive = min(sum(dish.dish_id in previous for dish in option) for option in choices)
            choices = [
                option for option in choices
                if sum(dish.dish_id in previous for dish in option) == minimum_consecutive
            ]

            minimum_usage = min(sum(usage_count.get(dish.dish_id, 0) for dish in option) for option in choices)
            choices = [
                option for option in choices
                if sum(usage_count.get(dish.dish_id, 0) for dish in option) == minimum_usage
            ]

            preferred = {tag.casefold() for tag in request.preferred_tags}
            methods_today = day_methods.setdefault(day, set())

            def final_score(option: tuple[DishCandidate, ...]) -> tuple[float, int]:
                quality = self._meal_nutrition_score(request, option)
                quality += sum(
                    usage_count.get(dish.dish_id, 0) * repeat_weights[dish.dish_type]
                    for dish in option
                )
                quality += sum(
                    self._policy.cooking_method_repeat_penalty
                    for dish in option if dish.cooking_method and dish.cooking_method in methods_today
                )
                quality -= sum(
                    self._policy.preferred_tag_bonus
                    for dish in option
                    if preferred.intersection(tag.casefold() for tag in dish.tags)
                )
                quality += sum(dish.estimated_cost for dish in option) / 1_000 * self._policy.cost_weight
                # Stable seed-dependent tie break; does not rely on Python's
                # randomized hash implementation.
                tie = sum((position + 1) * dish.dish_id for position, dish in enumerate(option))
                seeded_tie = sum(
                    (position + 1) * dish.dish_id * (seed_value + 97)
                    for position, dish in enumerate(option)
                )
                return quality, (tie + seeded_tie) % 1_000_003

            if index == len(positions) - 1 and previous_selection and not differs_from_previous:
                previous_ids = previous_selection.get((day, slot), set())
                different = [
                    option for option in choices
                    if {dish.dish_id for dish in option} != previous_ids
                ]
                if not different:
                    different = [
                        option for option in affordable
                        if {dish.dish_id for dish in option} != previous_ids
                    ]
                if different:
                    choices = different

            chosen = min(choices, key=final_score)
            ids = {dish.dish_id for dish in chosen}
            selected[(day, slot)] = ids
            if previous_selection and ids != previous_selection.get((day, slot), set()):
                differs_from_previous = True
            today.update(ids)
            for dish in chosen:
                usage_count[dish.dish_id] = usage_count.get(dish.dish_id, 0) + 1
                if dish.cooking_method:
                    methods_today.add(dish.cooking_method)
            spent += sum(dish.estimated_cost for dish in chosen)

        return selected

    @staticmethod
    def _hint_satisfies_regenerate_constraint(
        selection: dict[tuple[int, MealType], set[int]], signature: str | None
    ) -> bool:
        if not signature:
            return True
        old_count = 0
        still_selected = 0
        for item in signature.split("|"):
            try:
                day, slot, dish_id = item.split(":")
                key = (int(day) - 1, MealType(slot))
                parsed_dish_id = int(dish_id)
            except (TypeError, ValueError):
                continue
            old_count += 1
            still_selected += int(parsed_dish_id in selection.get(key, set()))
        return old_count == 0 or still_selected < old_count

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

    def _diversity_score_from_days(self, days: list[list[ComposedMeal]]) -> int:
        weights = {
            DishType.BREAKFAST: self._policy.breakfast_repeat_penalty,
            DishType.STAPLE: self._policy.staple_repeat_penalty,
            DishType.SAVORY: self._policy.savory_repeat_penalty,
            DishType.VEGETABLE_SIDE: self._policy.side_repeat_penalty,
            DishType.SOUP: self._policy.side_repeat_penalty,
        }
        usage: dict[int, tuple[DishType, int]] = {}
        score = 0
        previous_by_slot: dict[MealType, set[int]] = {}
        for day in days:
            today_by_slot: dict[MealType, set[int]] = {}
            for meal in day:
                ids = {dish.dish_id for dish in meal.dishes}
                today_by_slot[meal.slot] = ids
                for dish in meal.dishes:
                    dish_type, count = usage.get(dish.dish_id, (dish.dish_type, 0))
                    usage[dish.dish_id] = (dish_type, count + 1)
                score += len(ids.intersection(previous_by_slot.get(meal.slot, set()))) * self._policy.consecutive_repeat_penalty
            lunch = today_by_slot.get(MealType.LUNCH, set())
            dinner = today_by_slot.get(MealType.DINNER, set())
            score += len(lunch.intersection(dinner)) * self._policy.same_day_repeat_penalty
            previous_by_slot = today_by_slot
        score += sum(max(0, count - 1) * weights[dish_type] for dish_type, count in usage.values())
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
            # Nutrition and budget are already handled by previous phases / a
            # hard constraint.  Raw VND here previously dwarfed all diversity
            # penalties (e.g. 50 versus 10,000), making the quality objective
            # systematically pick the same cheap dish.  Thousand-VND keeps
            # cost as a final tie-breaker without undoing diversity.
            cost_in_thousands = int(round(candidate.estimated_cost / 1_000))
            parts.append(variable * cost_in_thousands * self._policy.cost_weight)
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
                # Plan snapshots expose human-friendly day numbers starting at
                # 1, while optimizer variables use zero-based day indexes.
                key = (int(day) - 1, MealType(slot), int(dish_id))
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

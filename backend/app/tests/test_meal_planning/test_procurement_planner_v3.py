from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from datetime import date
import time

import pytest

from app.core.exceptions import ConflictError
from app.modules.meal_planning.domain import (
    ComposedMeal,
    DishCandidate,
    DishIngredientSnapshot,
    InventoryLotSnapshot,
    PlanRequest,
)
from app.modules.meal_planning.optimizer_v3 import ProcurementCpSatOptimizer
from app.modules.meal_planning.planner import DishPlanner
from app.modules.meal_planning.procurement_checker import validate_v3
from app.modules.meal_planning.schemas import MealPlanCreate
from app.modules.meal_planning.use_cases import SaveMealPlanUseCase
from app.shared.enums import DishType, MealType


def plan_request(**changes) -> PlanRequest:
    values = {
        "user_id": 1,
        "days": 1,
        "meals_per_day": 2,
        "budget_limit": None,
        "target_calories": 1_000,
        "target_protein_g": 70,
        "target_fat_g": 32,
        "target_carb_g": 120,
    }
    values.update(changes)
    return PlanRequest(**values)


def ingredient(
    ingredient_id: int,
    quantity: float,
    *,
    mode: str = "regular",
    increment: float | None = 100,
    price: float | None = 10,
    room: int | None = 0,
    fridge: int | None = None,
    freezer: int | None = None,
    max_extra: float = 0,
    extra_step: float | None = None,
    calories_per_100g: float = 0,
) -> DishIngredientSnapshot:
    return DishIngredientSnapshot(
        ingredient_id=ingredient_id,
        name=f"Nguyên liệu {ingredient_id}",
        quantity=quantity,
        unit="g",
        estimated_cost=(quantity * price) if mode == "regular" and price is not None else 0,
        purchase_mode=mode,
        purchase_increment=increment if mode == "regular" else None,
        price_per_default_unit=price if mode == "regular" else None,
        grams_per_unit=1,
        calories_per_100g=calories_per_100g,
        room_shelf_life_days=room,
        fridge_shelf_life_days=fridge,
        freezer_shelf_life_days=freezer,
        max_extra_quantity=max_extra,
        extra_step_quantity=extra_step,
    )


def candidate(
    dish_id: int,
    dish_type: DishType,
    calories: float,
    protein: float,
    ingredients: tuple[DishIngredientSnapshot, ...],
) -> DishCandidate:
    return DishCandidate(
        dish_id=dish_id,
        name=f"Món {dish_id}",
        dish_type=dish_type,
        cooking_method=None,
        calories=calories,
        protein_g=protein,
        fat_g=16 / 3,
        carb_g=20,
        estimated_cost=sum(item.estimated_cost for item in ingredients),
        ingredient_ids=tuple(item.ingredient_id for item in ingredients),
        ingredients=ingredients,
    )


def fixed_catalog(
    days: int,
    ingredient_for_position,
    *,
    daily_calories: tuple[float, ...] = (100, 300, 100, 100, 300, 100),
) -> tuple[list[DishCandidate], list[list[ComposedMeal]]]:
    candidates: list[DishCandidate] = []
    fixed_days: list[list[ComposedMeal]] = []
    types = (
        DishType.STAPLE,
        DishType.SAVORY,
        DishType.VEGETABLE_SIDE,
        DishType.STAPLE,
        DishType.SAVORY,
        DishType.SOUP,
    )
    proteins = (5, 25, 5, 5, 25, 5)
    for day_index in range(days):
        day_dishes: list[DishCandidate] = []
        for position, dish_type in enumerate(types):
            dish_id = day_index * 10 + position + 1
            dish = candidate(
                dish_id,
                dish_type,
                daily_calories[position],
                proteins[position],
                tuple(ingredient_for_position(day_index, position, dish_id)),
            )
            candidates.append(dish)
            day_dishes.append(dish)
        fixed_days.append([
            ComposedMeal(MealType.LUNCH, tuple(day_dishes[:3])),
            ComposedMeal(MealType.DINNER, tuple(day_dishes[3:])),
        ])
    return candidates, fixed_days


def solve_fixed(
    request: PlanRequest,
    candidates: list[DishCandidate],
    fixed_days: list[list[ComposedMeal]],
):
    result = ProcurementCpSatOptimizer(timeout_seconds=3).solve(
        request, candidates, seed=7, fixed_days=fixed_days
    )
    assert result is not None
    assert validate_v3(result, request).is_feasible
    return result


def test_shared_demand_is_aggregated_before_rounding_to_purchase_blocks():
    candidates, days = fixed_catalog(
        1,
        lambda _day, _position, _dish_id: (ingredient(1, 20, room=2),),
    )

    result = solve_fixed(plan_request(), candidates, days)
    item = result.procurement_plan["purchase_items"][0]

    assert item["required_quantity"] == 120
    assert item["purchase_increment"] == 100
    assert item["block_count"] == 2
    assert item["purchase_quantity"] == 200
    assert item["purchase_cost"] == 2_000
    assert result.purchase_cost == 2_000


def test_pantry_is_a_zero_cost_check_and_ignored_is_not_a_shopping_item():
    def ingredients_for(_day, position, dish_id):
        if position == 0:
            return (
                ingredient(10, 2, mode="pantry"),
                ingredient(11, 1, mode="ignored"),
            )
        return (ingredient(100 + dish_id, 1, mode="ignored"),)

    candidates, days = fixed_catalog(1, ingredients_for)
    result = solve_fixed(plan_request(), candidates, days)

    assert result.purchase_cost == 0
    assert result.procurement_plan["purchase_items"] == []
    assert [(item["ingredient_id"], item["quantity"]) for item in result.procurement_plan["pantry_checks"]] == [(10, 2)]
    assert any(warning.code == "PANTRY_ASSUMED_AVAILABLE" for warning in result.warnings)


def test_same_day_shelf_life_forces_separate_daily_purchases():
    candidates, days = fixed_catalog(
        3,
        lambda _day, _position, _dish_id: (ingredient(1, 10, room=0),),
    )
    result = solve_fixed(plan_request(days=3), candidates, days)

    items = result.procurement_plan["purchase_items"]
    assert result.procurement_plan["shopping_days"] == [1, 2, 3]
    assert [(item["purchase_day"], item["block_count"]) for item in items] == [(1, 1), (2, 1), (3, 1)]
    assert all(
        allocation["day"] == item["purchase_day"]
        for item in items
        for allocation in item["allocations"]
    )


def test_jit_reuses_an_earlier_remainder_but_new_blocks_wait_for_same_day_use():
    candidates, days = fixed_catalog(
        2,
        lambda _day, _position, _dish_id: (
            ingredient(1, 10, room=0, fridge=2),
        ),
    )
    result = solve_fixed(plan_request(days=2), candidates, days)

    assert result.procurement_plan["shopping_days"] == [1, 2]
    assert result.purchase_cost == 2_000
    first, second = result.procurement_plan["purchase_items"]
    assert first["purchase_day"] == 1
    assert first["purchase_quantity"] == 100
    assert first["required_quantity"] == 100
    assert {allocation["day"] for allocation in first["allocations"]} == {1, 2}
    assert second["purchase_day"] == 2
    assert second["purchase_quantity"] == 100
    assert second["required_quantity"] == 20
    assert second["carryover_quantity"] == 80
    assert {allocation["day"] for allocation in second["allocations"]} == {2}


def test_purchase_waits_until_first_use_even_when_earlier_shopping_days_exist():
    def ingredients_for(day, position, dish_id):
        if position != 0:
            return (ingredient(1_000 + dish_id, 1, mode="ignored"),)
        if day == 0:
            return (ingredient(10, 10, room=0),)
        if day == 1:
            return (ingredient(11, 10, room=0),)
        return (ingredient(12, 220, room=5),)

    candidates, days = fixed_catalog(3, ingredients_for)
    result = solve_fixed(plan_request(days=3), candidates, days)

    target = [
        item
        for item in result.procurement_plan["purchase_items"]
        if item["ingredient_id"] == 12
    ]
    assert result.procurement_plan["shopping_days"] == [1, 2, 3]
    assert len(target) == 1
    assert target[0]["purchase_day"] == 3
    assert target[0]["purchase_quantity"] == 300
    assert target[0]["required_quantity"] == 220
    assert target[0]["carryover_quantity"] == 80
    assert [allocation["day"] for allocation in target[0]["allocations"]] == [3]


def test_jit_schedule_survives_timeout_before_waste_and_holding_phases(monkeypatch):
    def ingredients_for(day, position, dish_id):
        if position != 0:
            return (ingredient(1_000 + dish_id, 1, mode="ignored"),)
        if day < 2:
            return (ingredient(10 + day, 10, room=0),)
        return (ingredient(12, 220, room=5),)

    candidates, days = fixed_catalog(3, ingredients_for)
    request = plan_request(days=3, ledger_enabled=True)
    optimizer = ProcurementCpSatOptimizer(timeout_seconds=3)
    original_run_phase = optimizer._run_phase

    def interrupted(data, incumbent, objective, name, started, seed):
        if name == "expired_waste":
            return incumbent, False, False
        return original_run_phase(data, incumbent, objective, name, started, seed)

    monkeypatch.setattr(optimizer, "_run_phase", interrupted)
    result = optimizer.solve(request, candidates, seed=7, fixed_days=days)

    assert result is not None
    assert any(warning.code == "SOLVER_TIMEOUT_BEST_EFFORT" for warning in result.warnings)
    assert all(
        any(
            allocation["day"] == item["purchase_day"]
            and allocation["quantity"] > 0
            for allocation in item["allocations"]
        )
        for item in result.procurement_plan["purchase_items"]
    )
    assert all(
        not (
            row["source_kind"] == "purchase"
            and row["purchase_quantity"] > 0
            and row["usage_quantity"] == 0
        )
        for day in result.procurement_plan["daily_ledger"]
        for row in day["items"]
    )
    assert validate_v3(result, request).is_feasible


def test_small_leftover_is_absorbed_only_when_flexible_and_nutrition_improves():
    def ingredients_for(_day, position, dish_id):
        if position == 0:
            return (ingredient(1, 95, room=2, calories_per_100g=100),)
        if position == 5:
            return (
                ingredient(
                    1,
                    95,
                    room=2,
                    max_extra=10,
                    extra_step=5,
                    calories_per_100g=100,
                ),
            )
        return (ingredient(100 + dish_id, 1, mode="ignored"),)

    candidates, days = fixed_catalog(
        1,
        ingredients_for,
        daily_calories=(100, 295, 100, 100, 295, 100),
    )
    result = solve_fixed(plan_request(), candidates, days)

    assert len(result.adjustments) == 1
    adjustment = result.adjustments[0]
    assert adjustment["extra_quantity"] == 10
    assert adjustment["actual_quantity"] == 105
    assert result.base_nutrition[0]["calories"] == 990
    assert result.final_nutrition[0]["calories"] == 1_000
    item = result.procurement_plan["purchase_items"][0]
    assert item["remaining_quantity"] == 0
    assert item["block_count"] == 2


def test_calorie_dense_leftover_is_not_absorbed_past_the_daily_target():
    def ingredients_for(_day, position, dish_id):
        if position == 0:
            return (ingredient(1, 95, room=2, calories_per_100g=1_000),)
        if position == 5:
            return (
                ingredient(
                    1,
                    95,
                    room=2,
                    max_extra=10,
                    extra_step=5,
                    calories_per_100g=1_000,
                ),
            )
        return (ingredient(100 + dish_id, 1, mode="ignored"),)

    candidates, days = fixed_catalog(
        1,
        ingredients_for,
        daily_calories=(100, 295, 100, 100, 295, 100),
    )
    result = solve_fixed(plan_request(), candidates, days)

    assert result.adjustments == []
    assert result.final_nutrition[0]["calories"] == 990
    assert result.procurement_plan["purchase_items"][0]["remaining_quantity"] == 10


def test_independent_checker_rejects_tampered_block_balance():
    candidates, days = fixed_catalog(
        1,
        lambda _day, _position, _dish_id: (ingredient(1, 20, room=2),),
    )
    result = solve_fixed(plan_request(), candidates, days)
    tampered_procurement = deepcopy(result.procurement_plan)
    tampered_procurement["purchase_items"][0]["purchase_quantity"] = 199
    tampered = replace(result, procurement_plan=tampered_procurement)

    checked = validate_v3(tampered, plan_request())

    assert not checked.is_feasible
    assert any("PROC-BLOCK" in violation for violation in checked.hard_violations)


def test_independent_checker_rejects_purchase_without_same_day_use():
    candidates, days = fixed_catalog(
        1,
        lambda _day, _position, _dish_id: (ingredient(1, 20, room=2),),
    )
    request = plan_request(ledger_enabled=True)
    result = solve_fixed(request, candidates, days)
    tampered_procurement = deepcopy(result.procurement_plan)
    tampered_procurement["purchase_items"][0]["purchase_day"] = 0
    first_purchase_row = next(
        row
        for row in tampered_procurement["daily_ledger"][0]["items"]
        if row["source_kind"] == "purchase"
    )
    first_purchase_row["usage_quantity"] = 0
    tampered = replace(result, procurement_plan=tampered_procurement)

    checked = validate_v3(tampered, request)

    assert not checked.is_feasible
    assert any("PROC-JIT" in violation for violation in checked.hard_violations)
    assert any("LEDGER-JIT" in violation for violation in checked.hard_violations)


def test_ledger_uses_inventory_before_new_purchase_and_balances_day_end():
    candidates, days = fixed_catalog(
        1,
        lambda _day, _position, _dish_id: (ingredient(1, 20, room=2),),
    )
    request = plan_request(
        ledger_enabled=True,
        inventory_fingerprint="inventory-v1",
        inventory_lots=(InventoryLotSnapshot(
            lot_id=7, ingredient_id=1, name="Nguyên liệu 1", quantity=100,
            unit="g", purchase_increment=100, available_day=1, expiry_day=2,
            storage_mode="fridge", cost_basis_per_unit=10,
        ),),
    )

    result = solve_fixed(request, candidates, days)

    assert result.purchase_cost == 1_000
    assert result.procurement_plan["inventory_items"][0]["required_quantity"] == 100
    row = result.procurement_plan["daily_ledger"][0]["items"]
    assert sum(item["opening_quantity"] for item in row) == 100
    assert sum(item["purchase_quantity"] for item in row) == 100
    assert sum(item["usage_quantity"] for item in row) == 120
    assert sum(item["closing_quantity"] for item in row) == 80
    assert validate_v3(result, request).is_feasible


def test_jit_inventory_allocation_is_fefo_before_new_purchase():
    candidates, days = fixed_catalog(
        1,
        lambda _day, _position, _dish_id: (ingredient(1, 20, room=2),),
    )
    request = plan_request(
        ledger_enabled=True,
        inventory_fingerprint="inventory-fefo",
        inventory_lots=(
            InventoryLotSnapshot(
                lot_id=8, ingredient_id=1, name="Nguyên liệu 1", quantity=100,
                unit="g", purchase_increment=100, available_day=1, expiry_day=3,
                storage_mode="fridge", cost_basis_per_unit=10,
            ),
            InventoryLotSnapshot(
                lot_id=7, ingredient_id=1, name="Nguyên liệu 1", quantity=50,
                unit="g", purchase_increment=100, available_day=1, expiry_day=1,
                storage_mode="fridge", cost_basis_per_unit=10,
            ),
        ),
    )

    result = solve_fixed(request, candidates, days)

    assert result.procurement_plan["purchase_items"] == []
    by_lot = {
        item["inventory_lot_id"]: item["required_quantity"]
        for item in result.procurement_plan["inventory_items"]
    }
    assert by_lot == {7: 50, 8: 70}
    assert result.procurement_plan["cost_summary"]["inventory_consumption_value"] == 1_200
    assert validate_v3(result, request).is_feasible


def test_planner_blocks_incomplete_purchase_rules_instead_of_silent_v2_fallback():
    valid, _days = fixed_catalog(
        1,
        lambda _day, _position, _dish_id: (ingredient(1, 20, room=2),),
    )
    invalid = candidate(
        999,
        DishType.SAVORY,
        300,
        25,
        (ingredient(999, 20, increment=None, room=2),),
    )

    result = DishPlanner().generate(plan_request(), [*valid, invalid], seed=7)

    assert result.status == "infeasible"
    assert result.infeasible_reasons[0].code == "MISSING_PURCHASE_RULE"
    assert result.infeasible_reasons[0].details["ingredient_count"] == 1


def test_planner_diagnoses_budget_failure_caused_by_purchase_rounding():
    candidates = [
        candidate(1, DishType.STAPLE, 100, 5, (ingredient(1, 20, room=2),)),
        candidate(2, DishType.SAVORY, 300, 25, (ingredient(1, 20, room=2),)),
        candidate(3, DishType.VEGETABLE_SIDE, 100, 5, (ingredient(1, 20, room=2),)),
    ]
    request = plan_request(budget_limit=1_500)

    result = DishPlanner().generate(request, candidates, seed=7)

    assert result.status == "infeasible"
    reason = result.infeasible_reasons[0]
    assert reason.code == "BUDGET_PURCHASE_BLOCK_CONFLICT"
    assert reason.details == {
        "budget_limit": 1_500,
        "minimum_feasible_purchase_cost": 2_000,
        "budget_gap": 500,
    }


def test_planner_recovers_when_budgeted_search_times_out_but_jit_cost_fits():
    candidates, fixed_days = fixed_catalog(
        1,
        lambda _day, _position, _dish_id: (ingredient(1, 20, room=2),),
    )
    unconstrained_request = plan_request()
    fallback = solve_fixed(unconstrained_request, candidates, fixed_days)
    request = replace(unconstrained_request, budget_limit=10_000)

    class _BudgetTimeoutOptimizer:
        def solve(self, current_request, _candidates, **_kwargs):
            if current_request.budget_limit is not None:
                return None
            return fallback

        source_fingerprint = staticmethod(ProcurementCpSatOptimizer.source_fingerprint)

    planner = DishPlanner()
    planner._optimizer = _BudgetTimeoutOptimizer()

    result = planner.generate(request, candidates, seed=7)

    assert result.plan_data["algorithm_version"] == "dish-cpsat-procurement-v3-jit2"
    assert result.total_cost == 2_000
    assert result.total_cost <= request.budget_limit
    assert result.plan_data["source_fingerprint"] == (
        ProcurementCpSatOptimizer.source_fingerprint(request, fallback.days)
    )
    assert any(
        warning["code"] == "BUDGET_SEARCH_TIMEOUT_RECOVERED"
        for warning in result.plan_data["warnings"]
    )


def test_adequate_diversity_tier_avoids_repeats_when_catalog_is_large_enough():
    candidates: list[DishCandidate] = []
    dish_id = 1
    for dish_type, calories, protein in (
        (DishType.STAPLE, 100, 5),
        (DishType.SAVORY, 300, 25),
        (DishType.VEGETABLE_SIDE, 100, 5),
    ):
        for _ in range(6):
            candidates.append(
                candidate(
                    dish_id,
                    dish_type,
                    calories,
                    protein,
                    (ingredient(1_000 + dish_id, 1, mode="ignored"),),
                )
            )
            dish_id += 1

    request = plan_request(days=3)
    result = ProcurementCpSatOptimizer(timeout_seconds=3).solve(request, candidates, seed=9)

    assert result is not None
    assert result.diversity_tier == "adequate"
    selected = [dish.dish_id for day in result.days for meal in day for dish in meal.dishes]
    assert len(selected) == len(set(selected))
    assert validate_v3(result, request).is_feasible


def test_cp_hard_protein_does_not_round_up_past_checker_boundary():
    candidates, fixed_days = fixed_catalog(
        1,
        lambda _day, _position, dish_id: (
            ingredient(1_000 + dish_id, 1, mode="ignored"),
        ),
    )
    candidates = [replace(item, protein_g=10.4999) for item in candidates]
    by_id = {item.dish_id: item for item in candidates}
    fixed_days = [[
        ComposedMeal(
            meal.slot,
            tuple(by_id[dish.dish_id] for dish in meal.dishes),
        )
        for meal in fixed_days[0]
    ]]
    request = plan_request(target_protein_g=70)

    result = ProcurementCpSatOptimizer(timeout_seconds=3).solve(
        request, candidates, seed=7, fixed_days=fixed_days
    )

    assert sum(item.protein_g for item in candidates) == pytest.approx(62.9994)
    assert result is None


def _save_fixture(*, absorb_leftover: bool = False):
    def ingredients_for(_day, position, dish_id):
        if not absorb_leftover:
            return (ingredient(1, 20, room=2),)
        quantities = (45, 45, 5, 45, 45, 5)
        return (
            ingredient(
                1,
                quantities[position],
                room=2,
                max_extra=10 if position == 5 else 0,
                extra_step=5 if position == 5 else None,
                calories_per_100g=100,
            ),
        )

    calories = (100, 295, 100, 100, 295, 100) if absorb_leftover else (
        100, 300, 100, 100, 300, 100
    )
    candidates, composed = fixed_catalog(
        1,
        ingredients_for,
        daily_calories=calories,
    )
    request = plan_request()
    solved = solve_fixed(request, candidates, composed)
    entity = DishPlanner().build_entity(
        composed, request, date(2026, 7, 19), solved.warnings, solved
    )
    adjustment_lookup: dict[tuple[int, str], list[dict]] = {}
    for adjustment in entity.plan_data["adjustments"]:
        adjustment_lookup.setdefault(
            (int(adjustment["day"]), str(adjustment["slot"])), []
        ).append({
            "dish_id": adjustment["dish_id"],
            "ingredient_id": adjustment["ingredient_id"],
            "extra_quantity": adjustment["extra_quantity"],
        })
    payload = MealPlanCreate.model_validate({
        "name": "Plan V3 đã xác minh",
        "start_date": "2026-07-19",
        "budget_limit": request.budget_limit,
        "source_fingerprint": entity.plan_data["source_fingerprint"],
        "days": [
            {
                "day": day["day"],
                "meals": [
                    {
                        "slot": meal["meal_type"],
                        "dish_ids": [dish["dish_id"] for dish in meal["dishes"]],
                        "adjustments": adjustment_lookup.get(
                            (int(day["day"]), str(meal["meal_type"])), []
                        ),
                    }
                    for meal in day["meals"]
                ],
            }
            for day in entity.plan_data["days"]
        ],
    })
    return candidates, request, entity, payload


class _SaveProvider:
    def __init__(self, candidates):
        self.candidates = {item.dish_id: item for item in candidates}

    def load_by_ids(self, dish_ids):
        return {dish_id: self.candidates[dish_id] for dish_id in dish_ids if dish_id in self.candidates}


class _SaveRequestBuilder:
    def __init__(self, request):
        self.request = request

    def execute(self, _user_id, **changes):
        return replace(
            self.request,
            days=changes["days"],
            meals_per_day=changes["meals_per_day"],
            budget_limit=changes["budget_limit"],
        )


class _SaveRepository:
    def __init__(self):
        self.created = None

    def create(self, entity):
        self.created = entity
        return entity

    def commit(self):
        return None

    def rollback(self):
        return None


def test_save_v3_recomputes_and_persists_backend_owned_snapshot():
    candidates, request, generated, payload = _save_fixture()
    repository = _SaveRepository()

    saved = SaveMealPlanUseCase(
        repository, _SaveProvider(candidates), _SaveRequestBuilder(request)
    ).execute(payload, user_id=1)

    assert repository.created is saved
    assert saved.plan_data["schema_version"] == 3
    assert saved.plan_data["source_fingerprint"] == generated.plan_data["source_fingerprint"]
    assert saved.total_cost == 2_000
    assert saved.plan_data["cost_summary"]["purchase_cost"] == 2_000


def test_save_v3_rejects_tampered_leftover_adjustment():
    candidates, request, _generated, payload = _save_fixture(absorb_leftover=True)
    assert payload.days[0].meals[1].adjustments[0].extra_quantity == 10
    tampered = payload.model_copy(deep=True)
    tampered.days[0].meals[1].adjustments[0].extra_quantity = 5

    with pytest.raises(ConflictError, match="PLAN_ADJUSTMENTS_CHANGED"):
        SaveMealPlanUseCase(
            _SaveRepository(), _SaveProvider(candidates), _SaveRequestBuilder(request)
        ).execute(tampered, user_id=1)


def test_save_v3_rejects_changed_price_or_purchase_rule_fingerprint():
    candidates, request, _generated, payload = _save_fixture()
    changed_candidates = []
    for dish in candidates:
        changed_ingredients = tuple(
            replace(
                item,
                price_per_default_unit=11,
                estimated_cost=item.quantity * 11,
            )
            for item in dish.ingredients
        )
        changed_candidates.append(
            replace(
                dish,
                ingredients=changed_ingredients,
                estimated_cost=sum(item.estimated_cost for item in changed_ingredients),
            )
        )

    with pytest.raises(ConflictError, match="PLAN_SOURCE_CHANGED"):
        SaveMealPlanUseCase(
            _SaveRepository(), _SaveProvider(changed_candidates), _SaveRequestBuilder(request)
        ).execute(payload, user_id=1)


def test_v3_600_dish_seven_day_catalog_finishes_within_solver_budget():
    counts = (
        (DishType.BREAKFAST, 90, 400, 20, 40),
        (DishType.STAPLE, 45, 250, 5, 25),
        (DishType.SAVORY, 250, 350, 35, 35),
        (DishType.VEGETABLE_SIDE, 105, 150, 5, 15),
        (DishType.SOUP, 110, 150, 5, 15),
    )
    candidates: list[DishCandidate] = []
    dish_id = 1
    for dish_type, count, calories, protein, quantity in counts:
        for _ in range(count):
            candidates.append(
                candidate(
                    dish_id,
                    dish_type,
                    calories,
                    protein,
                    (ingredient(1, quantity, room=0, fridge=2),),
                )
            )
            dish_id += 1
    request = plan_request(
        days=7,
        meals_per_day=3,
        budget_limit=20_000,
        target_calories=1_900,
        target_protein_g=110,
        target_fat_g=70,
        target_carb_g=210,
    )

    started = time.perf_counter()
    result = ProcurementCpSatOptimizer(timeout_seconds=3).solve(request, candidates, seed=11)
    elapsed = time.perf_counter() - started

    assert result is not None
    assert elapsed < 4
    assert result.purchase_cost <= 20_000
    assert validate_v3(result, request).is_feasible

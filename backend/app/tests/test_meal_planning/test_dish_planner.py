from __future__ import annotations

import time
from itertools import product

from app.modules.meal_planning.constraint_checker import validate_plan
from app.modules.meal_planning.domain import ComposedMeal, DishCandidate, DishIngredientSnapshot, PlanRequest, QualityPolicy
from app.modules.meal_planning.planner import DishPlanner
from app.modules.meal_planning.optimizer import DishCpSatOptimizer
from app.modules.meal_planning.schemas import GenerateMealPlanRequest, MealPlanCreate
from app.modules.meal_planning.use_cases import SaveMealPlanUseCase
from app.modules.meal_planning.exceptions import InvalidMealSelectionError
from app.shared.enums import DishType, MealType


def dish(
    dish_id: int,
    dish_type: DishType,
    *,
    calories: float = 300,
    protein: float = 20,
    cost: float = 10_000,
    ingredient_id: int | None = None,
) -> DishCandidate:
    ingredient_id = ingredient_id or dish_id
    return DishCandidate(
        dish_id=dish_id,
        name=f"{dish_type.value}-{dish_id}",
        dish_type=dish_type,
        cooking_method=None,
        calories=calories,
        protein_g=protein,
        fat_g=10,
        carb_g=30,
        estimated_cost=cost,
        ingredient_ids=(ingredient_id,),
        ingredients=(DishIngredientSnapshot(ingredient_id, f"i-{ingredient_id}", 1, "g", cost),),
    )


def pool() -> list[DishCandidate]:
    return [
        dish(1, DishType.BREAKFAST, calories=350, protein=15),
        dish(2, DishType.BREAKFAST, calories=450, protein=25),
        dish(3, DishType.STAPLE, calories=250, protein=5),
        dish(4, DishType.STAPLE, calories=350, protein=8),
        dish(5, DishType.SAVORY, calories=400, protein=40),
        dish(6, DishType.SAVORY, calories=300, protein=25),
        dish(7, DishType.VEGETABLE_SIDE, calories=120, protein=6),
        dish(8, DishType.VEGETABLE_SIDE, calories=180, protein=8),
        dish(9, DishType.SOUP, calories=100, protein=5),
    ]


def request(**changes) -> PlanRequest:
    base = dict(
        user_id=1, days=1, meals_per_day=3, budget_limit=100_000,
        target_calories=1_800, target_protein_g=120, target_fat_g=60, target_carb_g=180,
    )
    base.update(changes)
    return PlanRequest(**base)


def test_main_meals_have_exactly_required_roles_and_snapshot_v2():
    result = DishPlanner().generate(request(), pool())
    assert result.plan_data["schema_version"] == 2
    meals = result.plan_data["days"][0]["meals"]
    assert [len(meal["dishes"]) for meal in meals] == [1, 3, 3]
    for meal in meals[1:]:
        assert sorted(dish["dish_type"] for dish in meal["dishes"]) in (
            ["savory", "soup", "staple"],
            ["savory", "staple", "vegetable_side"],
        )
        assert meal["candidate_type"] == "dynamic_meal"
        assert meal["dishes"][0]["ingredients"]


def test_global_budget_finds_cheap_combination_instead_of_greedy_false_infeasible():
    candidates = pool()
    expensive = dish(10, DishType.BREAKFAST, cost=80_000, calories=500, protein=40)
    candidates.append(expensive)
    # Cheapest 3-meal day costs 70k; expensive breakfast makes a sequential
    # heuristic fail late but CP-SAT selects a globally affordable combination.
    result = DishPlanner().generate(request(budget_limit=70_000), candidates)
    assert result.total_cost <= 70_000
    selected = [d["dish_id"] for m in result.plan_data["days"][0]["meals"] for d in m["dishes"]]
    assert expensive.dish_id not in selected


def test_precheck_reports_structured_minimum_budget():
    result = DishPlanner().generate(request(budget_limit=1), pool())
    assert result.status == "infeasible"
    reason = result.infeasible_reasons[0]
    assert reason.code == "BUDGET_BELOW_MINIMUM"
    assert reason.details["budget_gap"] > 0


def test_excluded_ingredient_never_appears_in_any_dish():
    result = DishPlanner().generate(request(excluded_ingredient_ids=[5]), pool())
    dish_ids = [dish_data["dish_id"] for meal in result.plan_data["days"][0]["meals"] for dish_data in meal["dishes"]]
    assert 5 not in dish_ids


def test_checker_rejects_both_soup_and_vegetable_or_missing_role():
    candidates = {candidate.dish_id: candidate for candidate in pool()}
    invalid = [[
        ComposedMeal(MealType.BREAKFAST, (candidates[1],)),
        ComposedMeal(MealType.LUNCH, (candidates[3], candidates[5], candidates[7], candidates[9])),
        ComposedMeal(MealType.DINNER, (candidates[3], candidates[5], candidates[7])),
    ]]
    checked = validate_plan(invalid, request())
    assert not checked.is_feasible
    assert any("HC-COMPOSITION" in violation for violation in checked.hard_violations)


def test_incomplete_dish_is_not_eligible():
    invalid_breakfast = DishCandidate(
        dish_id=100, name="bad", dish_type=DishType.BREAKFAST, cooking_method=None,
        calories=200, protein_g=10, fat_g=5, carb_g=20, estimated_cost=1000,
    )
    result = DishPlanner().generate(request(), [invalid_breakfast, *[d for d in pool() if d.dish_type != DishType.BREAKFAST]])
    assert result.status == "infeasible"
    assert result.infeasible_reasons[0].code == "MISSING_BREAKFAST"


def test_regenerate_changes_signature_without_worse_than_five_percent_nutrition_score():
    candidates = pool() + [
        dish(11, DishType.SAVORY, calories=401, protein=40),
        dish(12, DishType.VEGETABLE_SIDE, calories=121, protein=6),
    ]
    original = DishPlanner().generate(request(), candidates, seed=7)
    regenerated = DishPlanner().generate(
        request(previous_plan_signature=original.plan_data["plan_signature"]), candidates, seed=7
    )
    assert regenerated.plan_data["plan_signature"] != original.plan_data["plan_signature"]
    assert regenerated.plan_data["metrics"]["nutrition_score"] <= original.plan_data["metrics"]["nutrition_score"] * 1.05 + 1


def test_same_seed_produces_same_signature():
    first = DishPlanner().generate(request(), pool(), seed=42)
    second = DishPlanner().generate(request(), pool(), seed=42)
    assert first.plan_data["plan_signature"] == second.plan_data["plan_signature"]


def test_quality_phase_prefers_variety_over_small_cost_savings():
    """A diverse pool must not collapse to the cheapest repeated meal.

    Alternatives have identical nutrition but cost just 1,000 VND more.  This
    reproduces the production issue where raw-VND cost dominated repeat
    penalties and every day received the same breakfast, lunch and dinner.
    """
    candidates = [
        *(dish(index, DishType.BREAKFAST, calories=350, protein=20, cost=10_000 + index * 1_000) for index in range(1, 4)),
        *(dish(index, DishType.STAPLE, calories=250, protein=5, cost=10_000 + (index - 10) * 1_000) for index in range(10, 16)),
        *(dish(index, DishType.SAVORY, calories=350, protein=35, cost=10_000 + (index - 20) * 1_000) for index in range(20, 26)),
        *(dish(index, DishType.VEGETABLE_SIDE, calories=150, protein=5, cost=10_000 + (index - 30) * 1_000) for index in range(30, 36)),
    ]
    result = DishPlanner().generate(
        request(days=3, budget_limit=None, target_calories=2_000, target_protein_g=120),
        candidates,
        seed=17,
    )

    days = result.plan_data["days"]
    breakfasts = [day["meals"][0]["dishes"][0]["dish_id"] for day in days]
    assert len(set(breakfasts)) == 3
    selected_by_type: dict[str, list[int]] = {}
    for day in days:
        lunch_ids = {item["dish_id"] for item in day["meals"][1]["dishes"]}
        dinner_ids = {item["dish_id"] for item in day["meals"][2]["dishes"]}
        assert lunch_ids.isdisjoint(dinner_ids)
        for meal in day["meals"]:
            for item in meal["dishes"]:
                selected_by_type.setdefault(item["dish_type"], []).append(item["dish_id"])
    assert all(len(ids) == len(set(ids)) for ids in selected_by_type.values())


def test_small_cpsat_instance_matches_brute_force_nutrition_optimum():
    candidates = pool()
    plan_request = request()
    # Isolate the nutrition optimizer here. Diversity-first selection is
    # covered separately and may intentionally trade a small nutrition delta
    # to avoid repeating lunch at dinner.
    nutrition_only = QualityPolicy(
        savory_repeat_penalty=0,
        side_repeat_penalty=0,
        breakfast_repeat_penalty=0,
        staple_repeat_penalty=0,
        same_day_repeat_penalty=0,
        consecutive_repeat_penalty=0,
    )
    result = DishPlanner(policy=nutrition_only).generate(plan_request, candidates, seed=4)
    breakfasts = [candidate for candidate in candidates if candidate.dish_type == DishType.BREAKFAST]
    staples = [candidate for candidate in candidates if candidate.dish_type == DishType.STAPLE]
    savory = [candidate for candidate in candidates if candidate.dish_type == DishType.SAVORY]
    sides = [candidate for candidate in candidates if candidate.dish_type in (DishType.VEGETABLE_SIDE, DishType.SOUP)]

    def nutrition_score(selection):
        totals = {
            "calories": round(sum(candidate.calories for candidate in selection) * 10),
            "protein_g": round(sum(candidate.protein_g for candidate in selection) * 10),
            "fat_g": round(sum(candidate.fat_g for candidate in selection) * 10),
            "carb_g": round(sum(candidate.carb_g for candidate in selection) * 10),
        }
        return (
            abs(totals["calories"] - round(plan_request.target_calories * 10)) * 10
            + max(0, round(plan_request.target_protein_g * 10) - totals["protein_g"]) * 16
            + abs(totals["fat_g"] - round(plan_request.target_fat_g * 10)) * 3
            + abs(totals["carb_g"] - round(plan_request.target_carb_g * 10)) * 3
        )

    main_meals = list(product(staples, savory, sides))
    brute_force_optimum = min(
        nutrition_score((breakfast, *lunch, *dinner))
        for breakfast, lunch, dinner in product(breakfasts, main_meals, main_meals)
    )
    assert result.plan_data["metrics"]["nutrition_score"] == brute_force_optimum


def test_generate_and_save_schemas_reject_invalid_shapes():
    assert GenerateMealPlanRequest(days=1, meals_per_day=2, preferred_tags=["  nhanh ", "nhanh"]).preferred_tags == ["nhanh"]
    try:
        MealPlanCreate.model_validate({"start_date": "2026-01-01", "days": [{"day": 2, "meals": []}]})
    except ValueError:
        pass
    else:
        raise AssertionError("invalid save shape must be rejected")
    try:
        GenerateMealPlanRequest(days=8)
    except ValueError:
        pass
    else:
        raise AssertionError("days outside 1..7 must be rejected")


def test_save_reloads_dishes_validates_composition_and_persists_v2_snapshot():
    class Provider:
        def load_by_ids(self, dish_ids):
            candidates = {candidate.dish_id: candidate for candidate in pool()}
            return {dish_id: candidates[dish_id] for dish_id in dish_ids if dish_id in candidates}

    class Requests:
        def execute(self, *_args, **_kwargs):
            return request()

    class Repository:
        def create(self, entity):
            return entity

    data = MealPlanCreate.model_validate({
        "start_date": "2026-07-10",
        "days": [{"day": 1, "meals": [
            {"slot": "breakfast", "dish_ids": [1]},
            {"slot": "lunch", "dish_ids": [3, 5, 7]},
            {"slot": "dinner", "dish_ids": [4, 6, 9]},
        ]}],
    })
    entity = SaveMealPlanUseCase(Repository(), Provider(), Requests()).execute(data, user_id=1)
    assert entity.plan_data["schema_version"] == 2
    assert entity.plan_data["days"][0]["meals"][1]["dishes"][0]["dish_type"] == "staple"

    invalid = data.model_copy(update={
        "days": [data.days[0].model_copy(update={
            "meals": [data.days[0].meals[0], data.days[0].meals[1].model_copy(update={"dish_ids": [3, 5, 7, 9]}), data.days[0].meals[2]],
        })]
    })
    try:
        SaveMealPlanUseCase(Repository(), Provider(), Requests()).execute(invalid, user_id=1)
    except InvalidMealSelectionError:
        pass
    else:
        raise AssertionError("save must reject an invalid main-meal composition")


def test_50_dish_seven_day_benchmark_stays_under_500ms_p95():
    candidates = []
    for index in range(50):
        dish_type = (
            DishType.BREAKFAST if index < 8 else DishType.STAPLE if index < 16
            else DishType.SAVORY if index < 32 else DishType.VEGETABLE_SIDE if index < 42
            else DishType.SOUP
        )
        candidates.append(dish(
            index + 1, dish_type, calories=150 + index * 7,
            protein=5 + index % 30, cost=5_000 + index * 101,
        ))
    benchmark_request = request(days=7, budget_limit=None, target_calories=2_100, target_protein_g=130, target_fat_g=65, target_carb_g=250)
    samples = []
    for seed in range(10):
        result = DishPlanner().generate(benchmark_request, candidates, seed=seed)
        assert not hasattr(result, "infeasible_reasons")
        samples.append(result.plan_data["metrics"]["solver_time_ms"])
    assert max(samples) < 500


def test_600_dish_catalog_is_shortlisted_and_generates_under_one_second():
    counts = (
        (DishType.BREAKFAST, 90),
        (DishType.STAPLE, 45),
        (DishType.SAVORY, 250),
        (DishType.VEGETABLE_SIDE, 105),
        (DishType.SOUP, 110),
    )
    candidates = []
    dish_id = 1
    for dish_type, count in counts:
        for index in range(count):
            candidates.append(dish(
                dish_id,
                dish_type,
                calories=120 + index % 45 * 8,
                protein=5 + index % 35,
                cost=4_000 + index * 37,
            ))
            dish_id += 1

    plan_request = request(
        days=3,
        budget_limit=None,
        target_calories=2_400,
        target_protein_g=130,
        target_fat_g=70,
        target_carb_g=300,
    )
    optimizer = DishCpSatOptimizer()
    shortlist = optimizer._shortlist_candidates(plan_request, candidates)
    assert len(shortlist) <= 40

    started = time.perf_counter()
    result = DishPlanner().generate(plan_request, candidates, seed=9)
    elapsed_ms = (time.perf_counter() - started) * 1_000
    assert elapsed_ms < 1_000
    assert all(count == 0 for count in result.plan_data["metrics"]["repeat_counts"].values())

"""Tiền kiểm rẻ, có lý do cụ thể trước khi gọi CP-SAT."""
from __future__ import annotations

from dataclasses import dataclass, field

from app.modules.meal_planning.domain import DishCandidate, InfeasibleReason, PlanRequest, StructuredWarning
from app.shared.enums import DishType


@dataclass(frozen=True)
class FeasibilityAssessment:
    infeasible_reasons: list[InfeasibleReason] = field(default_factory=list)
    warnings: list[StructuredWarning] = field(default_factory=list)
    minimum_required_budget: float = 0.0

    @property
    def is_feasible(self) -> bool:
        return not self.infeasible_reasons


def _by_type(candidates: list[DishCandidate]) -> dict[DishType, list[DishCandidate]]:
    result = {dish_type: [] for dish_type in DishType}
    for candidate in candidates:
        result[candidate.dish_type].append(candidate)
    return result


def _minimum_main_cost(pools: dict[DishType, list[DishCandidate]]) -> float:
    side = pools[DishType.VEGETABLE_SIDE] + pools[DishType.SOUP]
    return min(d.estimated_cost for d in pools[DishType.STAPLE]) + min(
        d.estimated_cost for d in pools[DishType.SAVORY]
    ) + min(d.estimated_cost for d in side)


def _daily_range(pools: dict[DishType, list[DishCandidate]], attribute: str, meals_per_day: int) -> tuple[float, float]:
    def value(d: DishCandidate) -> float:
        return float(getattr(d, attribute))

    main_min = min(value(d) for d in pools[DishType.STAPLE]) + min(value(d) for d in pools[DishType.SAVORY]) + min(
        value(d) for d in pools[DishType.VEGETABLE_SIDE] + pools[DishType.SOUP]
    )
    main_max = max(value(d) for d in pools[DishType.STAPLE]) + max(value(d) for d in pools[DishType.SAVORY]) + max(
        value(d) for d in pools[DishType.VEGETABLE_SIDE] + pools[DishType.SOUP]
    )
    if meals_per_day == 2:
        return main_min * 2, main_max * 2
    return (
        main_min * 2 + min(value(d) for d in pools[DishType.BREAKFAST]),
        main_max * 2 + max(value(d) for d in pools[DishType.BREAKFAST]),
    )


def assess(candidates: list[DishCandidate], request: PlanRequest) -> FeasibilityAssessment:
    pools = _by_type(candidates)
    missing: list[InfeasibleReason] = []
    if request.meals_per_day == 3 and not pools[DishType.BREAKFAST]:
        missing.append(InfeasibleReason("MISSING_BREAKFAST", "Không có món breakfast planner-ready."))
    for dish_type, code, label in (
        (DishType.STAPLE, "MISSING_STAPLE", "món tinh bột"),
        (DishType.SAVORY, "MISSING_SAVORY", "món mặn"),
    ):
        if not pools[dish_type]:
            missing.append(InfeasibleReason(code, f"Không có {label} planner-ready."))
    if not pools[DishType.VEGETABLE_SIDE] and not pools[DishType.SOUP]:
        missing.append(InfeasibleReason("MISSING_SIDE", "Không có món rau hoặc canh planner-ready."))
    if missing:
        return FeasibilityAssessment(infeasible_reasons=missing)

    minimum_daily_cost = _minimum_main_cost(pools) * 2
    if request.meals_per_day == 3:
        minimum_daily_cost += min(d.estimated_cost for d in pools[DishType.BREAKFAST])
    minimum_required_budget = minimum_daily_cost * request.days
    if request.budget_limit is not None and request.budget_limit + 1e-6 < minimum_required_budget:
        return FeasibilityAssessment(
            infeasible_reasons=[
                InfeasibleReason(
                    "BUDGET_BELOW_MINIMUM",
                    "Ngân sách thấp hơn chi phí tối thiểu để ghép đủ các bữa bắt buộc.",
                    {
                        "current_budget": round(request.budget_limit, 0),
                        "minimum_required_budget": round(minimum_required_budget, 0),
                        "budget_gap": round(minimum_required_budget - request.budget_limit, 0),
                    },
                )
            ],
            minimum_required_budget=minimum_required_budget,
        )

    warnings: list[StructuredWarning] = []
    targets = (
        ("calories", request.target_calories, "CALORIE_TARGET_UNATTAINABLE"),
        ("protein_g", request.target_protein_g, "PROTEIN_TARGET_UNATTAINABLE"),
        ("fat_g", request.target_fat_g, "FAT_TARGET_UNATTAINABLE"),
        ("carb_g", request.target_carb_g, "CARB_TARGET_UNATTAINABLE"),
    )
    for attribute, target, code in targets:
        low, high = _daily_range(pools, attribute, request.meals_per_day)
        if target and not low <= target <= high:
            warnings.append(
                StructuredWarning(
                    code,
                    f"Mục tiêu {attribute} nằm ngoài khoảng có thể đạt từ dữ liệu hiện tại.",
                    {"target": round(target, 1), "minimum": round(low, 1), "maximum": round(high, 1)},
                )
            )
    if len(pools[DishType.STAPLE]) <= 2:
        warnings.append(
            StructuredWarning(
                "LIMITED_STAPLE_VARIETY",
                "Số món tinh bột hiện có hạn chế nên planner sẽ cho phép lặp nhiều hơn.",
                {"available_count": len(pools[DishType.STAPLE])},
            )
        )
    if request.budget_limit is not None and request.budget_limit <= minimum_required_budget * 1.1:
        warnings.append(
            StructuredWarning(
                "BUDGET_NEAR_MINIMUM",
                "Ngân sách chỉ nhỉnh hơn mức tối thiểu; không gian tối ưu sẽ hạn chế.",
                {"minimum_required_budget": round(minimum_required_budget, 0)},
            )
        )
    return FeasibilityAssessment(warnings=warnings, minimum_required_budget=minimum_required_budget)

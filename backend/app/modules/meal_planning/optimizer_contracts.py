from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.modules.meal_planning.domain import ComposedMeal, StructuredWarning


@dataclass(frozen=True)
class V3OptimizationResult:
    days: list[list[ComposedMeal]]
    nutrition_score: int
    solver_time_ms: int
    solver_status: str
    timed_out_with_solution: bool
    procurement_plan: dict[str, Any]
    adjustments: list[dict[str, Any]]
    base_nutrition: list[dict[str, float]]
    final_nutrition: list[dict[str, float]]
    warnings: list[StructuredWarning]
    diversity_tier: str
    source_fingerprint: str

    @property
    def purchase_cost(self) -> float:
        return float(self.procurement_plan["cost_summary"]["purchase_cost"])

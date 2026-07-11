from __future__ import annotations

import json
from collections.abc import Iterable

from sqlalchemy import text

from app.modules.meal_planning.domain import DishCandidate, DishIngredientSnapshot
from app.modules.meal_planning.ports import DishCandidateProviderPort
from app.shared.enums import CookingMethod, DishType


_SELECT = """
    SELECT v.id, v.name, v.dish_type, v.cooking_method, v.tags,
           v.total_calories, v.total_protein_g, v.total_carbs_g, v.total_fat_g,
           v.estimated_cost, v.ingredient_ids, v.ingredients
    FROM v_dish_candidates v
"""


def _float(value) -> float:
    return float(value) if value is not None else 0.0


def _json(value, default):
    if value is None:
        return default
    if isinstance(value, str):
        return json.loads(value)
    return value


class SqlDishCandidateProvider(DishCandidateProviderPort):
    """Đọc dish planner-ready trực tiếp từ view.

    `ingredients` đã aggregate JSON trong view nên mỗi public method chỉ dùng một
    query, không có N+1 theo dish hoặc ingredient.
    """

    def __init__(self, session) -> None:
        self._session = session

    def load_candidates(self, excluded_ingredient_ids: list[int]) -> list[DishCandidate]:
        sql = _SELECT + " WHERE TRUE"
        params: dict[str, list[int]] = {}
        if excluded_ingredient_ids:
            sql += """
                AND NOT EXISTS (
                    SELECT 1 FROM dish_ingredients di
                    WHERE di.dish_id = v.id AND di.ingredient_id = ANY(:excluded)
                )
            """
            params["excluded"] = list(dict.fromkeys(excluded_ingredient_ids))
        sql += " ORDER BY v.id"
        return self._build(self._session.execute(text(sql), params).fetchall())

    def load_by_ids(self, dish_ids: list[int]) -> dict[int, DishCandidate]:
        ids = list(dict.fromkeys(dish_ids))
        if not ids:
            return {}
        rows = self._session.execute(
            text(_SELECT + " WHERE v.id = ANY(:ids) ORDER BY v.id"), {"ids": ids}
        ).fetchall()
        return {candidate.dish_id: candidate for candidate in self._build(rows)}

    def _build(self, rows: Iterable) -> list[DishCandidate]:
        result: list[DishCandidate] = []
        for row in rows:
            raw_ingredients = _json(row.ingredients, [])
            ingredients = tuple(
                DishIngredientSnapshot(
                    ingredient_id=int(ingredient["ingredient_id"]),
                    name=str(ingredient["name"]),
                    quantity=_float(ingredient["quantity"]),
                    unit=str(ingredient["unit"]),
                    estimated_cost=_float(ingredient["estimated_cost"]),
                )
                for ingredient in raw_ingredients
            )
            result.append(
                DishCandidate(
                    dish_id=int(row.id),
                    name=str(row.name),
                    dish_type=DishType(str(row.dish_type)),
                    cooking_method=CookingMethod(str(row.cooking_method)) if row.cooking_method else None,
                    calories=_float(row.total_calories),
                    protein_g=_float(row.total_protein_g),
                    fat_g=_float(row.total_fat_g),
                    carb_g=_float(row.total_carbs_g),
                    estimated_cost=_float(row.estimated_cost),
                    ingredient_ids=tuple(int(item) for item in _json(row.ingredient_ids, [])),
                    ingredients=ingredients,
                    tags=tuple(str(tag) for tag in _json(row.tags, [])),
                )
            )
        return result

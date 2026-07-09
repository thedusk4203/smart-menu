from __future__ import annotations

from sqlalchemy import text

from app.modules.meal_planning.domain import MealCandidate
from app.modules.meal_planning.ports import MealCandidateProviderPort

_SELECT = """
    SELECT v.id, v.name, v.meal_type, v.total_calories, v.total_protein_g,
           v.total_carbs_g, v.total_fat_g, v.estimated_cost, v.tags,
           v.dishes, v.components
    FROM v_meal_candidates v
"""


def _f(v) -> float:
    return float(v) if v is not None else 0.0


class SqlMealCandidateProvider(MealCandidateProviderPort):
    """Đọc mâm cơm hợp lệ (đang active) từ v_meal_candidates.

    Một candidate là một meal_set; nguyên liệu để loại trừ/tái sử dụng lấy từ
    meal_set_dishes -> dish_ingredients (union nguyên liệu của mọi dish).
    """

    def __init__(self, session) -> None:
        self._session = session

    def load_candidates(self, excluded_ingredient_ids: list[int]) -> list[MealCandidate]:
        # Loại mâm có chứa nguyên liệu bị loại trừ (qua bất kỳ dish nào) ở tầng SQL.
        sql = _SELECT + " WHERE TRUE"
        params: dict = {}
        if excluded_ingredient_ids:
            sql += """
              AND NOT EXISTS (
                  SELECT 1 FROM meal_set_dishes msd
                  JOIN dish_ingredients di ON di.dish_id = msd.dish_id
                  WHERE msd.meal_set_id = v.id
                    AND di.ingredient_id = ANY(:excluded)
              )
            """
            params["excluded"] = list(excluded_ingredient_ids)
        sql += " ORDER BY v.id"
        rows = self._session.execute(text(sql), params).fetchall()
        return self._build(rows)

    def load_by_ids(self, meal_set_ids: list[int]) -> dict[int, MealCandidate]:
        """Reload mâm cơm theo id — dùng khi LƯU để recompute totals từ nguồn
        đúng (v_meal_candidates), KHÔNG tin số liệu client gửi. Id không active
        / không tồn tại sẽ vắng mặt trong dict trả về (caller tự phát hiện)."""
        ids = list(dict.fromkeys(meal_set_ids))  # dedupe, giữ thứ tự
        if not ids:
            return {}
        rows = self._session.execute(
            text(_SELECT + " WHERE v.id = ANY(:ids)"), {"ids": ids}
        ).fetchall()
        return {c.meal_id: c for c in self._build(rows)}

    def _build(self, rows) -> list[MealCandidate]:
        if not rows:
            return []
        meal_set_ids = [r.id for r in rows]

        # ingredient_ids (union theo mâm) — một truy vấn, tránh N+1.
        ing_rows = self._session.execute(
            text(
                """SELECT DISTINCT msd.meal_set_id, di.ingredient_id
                     FROM meal_set_dishes msd
                     JOIN dish_ingredients di ON di.dish_id = msd.dish_id
                     WHERE msd.meal_set_id = ANY(:ids)"""
            ),
            {"ids": meal_set_ids},
        ).fetchall()
        ingredients_by_set: dict[int, list[int]] = {mid: [] for mid in meal_set_ids}
        for ir in ing_rows:
            ingredients_by_set.setdefault(ir.meal_set_id, []).append(ir.ingredient_id)

        # view total_carbs_g -> domain total_carb_g; meal_id = meal_set.id.
        return [
            MealCandidate(
                meal_id=r.id,
                name=r.name,
                meal_type=str(r.meal_type),
                total_calories=_f(r.total_calories),
                total_protein_g=_f(r.total_protein_g),
                total_fat_g=_f(r.total_fat_g),
                total_carb_g=_f(r.total_carbs_g),
                estimated_cost=_f(r.estimated_cost),
                ingredient_ids=ingredients_by_set.get(r.id, []),
                tags=list(r.tags) if r.tags else [],
                components=list(r.components) if r.components else [],
                dishes=list(r.dishes) if r.dishes else [],
            )
            for r in rows
        ]

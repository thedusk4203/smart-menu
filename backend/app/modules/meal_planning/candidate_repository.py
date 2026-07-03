from __future__ import annotations

from sqlalchemy import text

from app.modules.meal_planning.domain import MealCandidate
from app.modules.meal_planning.ports import MealCandidateProviderPort


def _f(v) -> float:
    return float(v) if v is not None else 0.0


class SqlMealCandidateProvider(MealCandidateProviderPort):
    """Đọc món hợp lệ (đang active) từ v_meals_full + meal_ingredients."""

    def __init__(self, session) -> None:
        self._session = session

    def load_candidates(self, excluded_ingredient_ids: list[int]) -> list[MealCandidate]:
        # 1) Lấy tổng hợp dinh dưỡng + chi phí + tags từ view; loại các món có chứa nguyên liệu bị loại trừ ngay ở tầng SQL.
        sql = """
            SELECT v.id, v.name, v.meal_type, v.total_calories, v.total_protein_g,
                   v.total_carbs_g, v.total_fat_g, v.estimated_cost, v.tags
            FROM v_meals_full v
            WHERE v.is_active = TRUE
        """
        params: dict = {}
        if excluded_ingredient_ids:
            sql += """
              AND NOT EXISTS (
                  SELECT 1 FROM meal_ingredients mi
                  WHERE mi.meal_id = v.id
                    AND mi.ingredient_id = ANY(:excluded)
              )
            """
            params["excluded"] = list(excluded_ingredient_ids)
        sql += " ORDER BY v.id"

        rows = self._session.execute(text(sql), params).fetchall()
        if not rows:
            return []

        meal_ids = [r.id for r in rows]

        # 2) Lấy ingredient_ids cho tất cả món trong một truy vấn (tránh N+1).
        ing_rows = self._session.execute(
            text(
                """SELECT meal_id, ingredient_id
                     FROM meal_ingredients
                     WHERE meal_id = ANY(:ids)"""
            ),
            {"ids": meal_ids},
        ).fetchall()
        ingredients_by_meal: dict[int, list[int]] = {mid: [] for mid in meal_ids}
        for ir in ing_rows:
            ingredients_by_meal.setdefault(ir.meal_id, []).append(ir.ingredient_id)

        # 3) Dựng MealCandidate. Lưu ý: view dùng cột total_carbs_g, domain dùng total_carb_g — ánh xạ tại đây.
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
                ingredient_ids=ingredients_by_meal.get(r.id, []),
                tags=list(r.tags) if r.tags else [],
            )
            for r in rows
        ]

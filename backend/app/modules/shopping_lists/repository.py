from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import text


class SqlLegacyDishRecipeProvider:
    """Chỉ phục vụ plan V1; plan V2 luôn đọc snapshot, không đọc recipe hiện tại."""

    def __init__(self, session) -> None:
        self._session = session

    def load_ingredients(self, dish_ids: list[int]) -> list[dict]:
        if not dish_ids:
            return []
        rows = self._session.execute(
            text(
                """SELECT di.dish_id, di.ingredient_id, i.name, di.quantity, di.unit,
                          COALESCE(di.quantity * lp.price_per_default_unit, 0) AS estimated_cost
                   FROM dish_ingredients di
                   JOIN ingredients i ON i.id = di.ingredient_id
                   LEFT JOIN LATERAL (
                       SELECT price_per_default_unit FROM price_snapshots ps
                       WHERE ps.ingredient_id = di.ingredient_id
                       ORDER BY ps.recorded_at DESC LIMIT 1
                   ) lp ON TRUE
                   WHERE di.dish_id = ANY(:dish_ids)
                   ORDER BY di.dish_id, di.id"""
            ),
            {"dish_ids": dish_ids},
        ).fetchall()
        return [
            {
                "dish_id": row.dish_id,
                "ingredient_id": row.ingredient_id,
                "name": row.name,
                "quantity": float(row.quantity),
                "unit": row.unit,
                "estimated_cost": float(row.estimated_cost),
            }
            for row in rows
        ]


class SqlShoppingListRepository:
    """Materializes the immutable plan snapshot once, while preserving checks."""

    def __init__(self, session) -> None:
        self._session = session

    def ensure_items(self, plan_id: int, items: list[dict]) -> list[dict]:
        existing = self.list_items(plan_id)
        if existing or not items:
            return existing
        for item in items:
            self._session.execute(
                text("""INSERT INTO shopping_lists
                         (meal_plan_id, ingredient_id, total_quantity, unit, estimated_cost)
                         VALUES (:plan_id, :ingredient_id, :quantity, :unit, :estimated_cost)"""),
                {"plan_id": plan_id, **item},
            )
        self._session.commit()
        return self.list_items(plan_id)

    def list_items(self, plan_id: int) -> list[dict]:
        rows = self._session.execute(
            text("""SELECT sl.id, sl.ingredient_id, i.name, sl.total_quantity AS quantity,
                          sl.unit, sl.estimated_cost, sl.is_purchased
                   FROM shopping_lists sl JOIN ingredients i ON i.id = sl.ingredient_id
                   WHERE sl.meal_plan_id = :plan_id ORDER BY i.name, sl.unit"""),
            {"plan_id": plan_id},
        ).fetchall()
        return [dict(row._mapping) for row in rows]

    def set_purchased(self, plan_id: int, item_id: int, purchased: bool) -> dict | None:
        row = self._session.execute(
            text("""UPDATE shopping_lists SET is_purchased = :purchased
                    WHERE id = :item_id AND meal_plan_id = :plan_id
                    RETURNING id, ingredient_id, total_quantity AS quantity, unit, estimated_cost, is_purchased"""),
            {"plan_id": plan_id, "item_id": item_id, "purchased": purchased},
        ).first()
        self._session.commit()
        return dict(row._mapping) if row else None


class SqlShoppingShareRepository:
    def __init__(self, session) -> None:
        self._session = session

    def get_or_create(self, plan_id: int) -> dict:
        row = self._session.execute(
            text("""SELECT * FROM shopping_list_shares WHERE meal_plan_id = :plan_id
                    AND revoked_at IS NULL ORDER BY created_at DESC LIMIT 1"""),
            {"plan_id": plan_id},
        ).first()
        now = datetime.now(timezone.utc)
        if row:
            data = dict(row._mapping)
            if data["expires_at"] > now:
                return data
            self._session.execute(text("UPDATE shopping_list_shares SET revoked_at = NOW() WHERE id=:id"), {"id": data["id"]})
        share_id = str(uuid4())
        expires_at = now + timedelta(days=7)
        created = self._session.execute(
            text("""INSERT INTO shopping_list_shares (id, meal_plan_id, expires_at)
                    VALUES (CAST(:id AS uuid), :plan_id, :expires_at) RETURNING *"""),
            {"id": share_id, "plan_id": plan_id, "expires_at": expires_at},
        ).first()
        self._session.commit()
        return dict(created._mapping)

    def get_active(self, share_id: str) -> dict | None:
        row = self._session.execute(
            text("""SELECT s.*, p.name AS plan_name FROM shopping_list_shares s
                    JOIN meal_plans p ON p.id=s.meal_plan_id
                    WHERE s.id=CAST(:id AS uuid) AND s.revoked_at IS NULL"""),
            {"id": share_id},
        ).first()
        return dict(row._mapping) if row else None

    def revoke(self, plan_id: int) -> None:
        self._session.execute(
            text("UPDATE shopping_list_shares SET revoked_at=NOW() WHERE meal_plan_id=:plan_id AND revoked_at IS NULL"),
            {"plan_id": plan_id},
        )
        self._session.commit()

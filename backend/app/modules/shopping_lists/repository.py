from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import text

from app.modules.shopping_lists.ports import ShoppingListRepositoryPort, ShoppingShareRepositoryPort


class SqlShoppingListRepository(ShoppingListRepositoryPort):
    """Materializes the immutable plan snapshot once, while preserving checks."""

    def __init__(self, session) -> None:
        self._session = session

    def ensure_items(self, plan_id: int, items: list[dict]) -> list[dict]:
        for item in items:
            item_key = item.get("item_key") or f"purchase:{item['ingredient_id']}:{item['unit']}"
            self._session.execute(
                text("""INSERT INTO shopping_lists
                         (meal_plan_id, ingredient_id, total_quantity, unit, estimated_cost,
                          item_key, item_kind, scheduled_day)
                         VALUES (:plan_id, :ingredient_id, :quantity, :unit, :estimated_cost,
                                 :item_key, :item_kind, :scheduled_day)
                         ON CONFLICT (meal_plan_id, item_key) DO UPDATE SET
                           ingredient_id=EXCLUDED.ingredient_id,
                           total_quantity=EXCLUDED.total_quantity,
                           unit=EXCLUDED.unit,
                           estimated_cost=EXCLUDED.estimated_cost,
                           item_kind=EXCLUDED.item_kind,
                           scheduled_day=EXCLUDED.scheduled_day"""),
                {
                    "plan_id": plan_id,
                    "ingredient_id": item["ingredient_id"],
                    "quantity": item["quantity"],
                    "unit": item["unit"],
                    "estimated_cost": item.get("estimated_cost", 0),
                    "item_key": item_key,
                    "item_kind": item.get("item_kind", "purchase"),
                    "scheduled_day": item.get("scheduled_day"),
                },
            )
        return self.list_items(plan_id)

    def list_items(self, plan_id: int) -> list[dict]:
        rows = self._session.execute(
            text("""SELECT sl.id, sl.ingredient_id, i.name, sl.total_quantity AS quantity,
                          sl.unit, sl.estimated_cost, sl.is_purchased,
                          sl.item_key, sl.item_kind, sl.scheduled_day
                   FROM shopping_lists sl JOIN ingredients i ON i.id = sl.ingredient_id
                   WHERE sl.meal_plan_id = :plan_id
                   ORDER BY COALESCE(sl.scheduled_day, 0), i.name, sl.unit"""),
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
        return dict(row._mapping) if row else None


class SqlShoppingShareRepository(ShoppingShareRepositoryPort):
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

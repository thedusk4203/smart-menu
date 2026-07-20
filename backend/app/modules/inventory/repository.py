from __future__ import annotations

import hashlib
import json
from datetime import date, timedelta

from sqlalchemy import text

from app.core.exceptions import ConflictError, NotFoundError, ValidationAppError
from app.modules.meal_planning.domain import InventoryLotSnapshot, MealPlanEntity


class SqlInventoryRepository:
    def __init__(self, session) -> None:
        self._session = session

    def snapshots_for_plan(
        self, user_id: int, start_date: date, end_date: date
    ) -> tuple[tuple[InventoryLotSnapshot, ...], str]:
        rows = self._session.execute(
            text(
                """SELECT l.id, l.ingredient_id, i.name, l.quantity_remaining,
                          l.unit, l.purchase_increment, l.available_from, l.expires_on,
                          l.storage_mode, l.cost_basis_per_unit, l.updated_at
                   FROM inventory_lots l
                   JOIN ingredients i ON i.id = l.ingredient_id
                   WHERE l.user_id = :user_id
                     AND l.quantity_remaining > 0
                     AND l.status IN ('projected', 'available')
                     AND l.available_from <= :end_date
                     AND l.expires_on >= :start_date
                   ORDER BY l.expires_on, l.id"""
            ),
            {"user_id": user_id, "start_date": start_date, "end_date": end_date},
        ).fetchall()
        snapshots = tuple(
            InventoryLotSnapshot(
                lot_id=int(row.id),
                ingredient_id=int(row.ingredient_id),
                name=str(row.name),
                quantity=float(row.quantity_remaining),
                unit=str(row.unit),
                purchase_increment=float(row.purchase_increment),
                available_day=max(1, (row.available_from - start_date).days + 1),
                expiry_day=(row.expires_on - start_date).days + 1,
                storage_mode=str(row.storage_mode),
                cost_basis_per_unit=float(row.cost_basis_per_unit),
            )
            for row in rows
            if row.expires_on >= start_date
        )
        fingerprint_payload = [
            {
                "id": int(row.id),
                "quantity": float(row.quantity_remaining),
                "available_from": row.available_from.isoformat(),
                "expires_on": row.expires_on.isoformat(),
                "updated_at": row.updated_at.isoformat(),
            }
            for row in rows
        ]
        fingerprint = hashlib.sha256(
            json.dumps(fingerprint_payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        return snapshots, fingerprint

    def verify_fingerprint(
        self, user_id: int, start_date: date, end_date: date, expected: str | None
    ) -> None:
        _lots, current = self.snapshots_for_plan(user_id, start_date, end_date)
        if expected is not None and current != expected:
            raise ConflictError(
                "INVENTORY_CHANGED: Kho nguyên liệu đã đổi; hãy tạo lại thực đơn."
            )

    def reserve_inputs(self, plan: MealPlanEntity) -> None:
        if plan.id is None:
            raise ValueError("Plan phải được flush trước khi giữ kho")
        inventory_items = plan.plan_data.get("procurement", {}).get("inventory_items", [])
        for item in inventory_items:
            allocations_by_day: dict[int, float] = {}
            for allocation in item.get("allocations", []):
                day = int(allocation["day"])
                allocations_by_day[day] = allocations_by_day.get(day, 0.0) + float(
                    allocation["quantity"]
                )
            required = round(sum(allocations_by_day.values()), 2)
            if required <= 0:
                continue
            row = self._session.execute(
                text(
                    """SELECT id, user_id, quantity_remaining
                       FROM inventory_lots WHERE id=:id FOR UPDATE"""
                ),
                {"id": int(item["inventory_lot_id"])},
            ).first()
            if row is None or int(row.user_id) != plan.user_id:
                raise ConflictError("INVENTORY_CHANGED: Lot kho không còn khả dụng.")
            if float(row.quantity_remaining) + 1e-6 < required:
                raise ConflictError("INVENTORY_CHANGED: Số lượng kho không còn đủ.")
            self._session.execute(
                text(
                    """UPDATE inventory_lots
                       SET quantity_remaining=quantity_remaining-:quantity,
                           status=CASE WHEN quantity_remaining-:quantity <= 0
                               THEN 'consumed' ELSE status END,
                           updated_at=NOW()
                       WHERE id=:id"""
                ),
                {"id": int(item["inventory_lot_id"]), "quantity": required},
            )
            for day, quantity in sorted(allocations_by_day.items()):
                self._session.execute(
                    text(
                        """INSERT INTO inventory_reservations
                           (inventory_lot_id, meal_plan_id, item_key, quantity, use_day)
                           VALUES (:lot_id, :plan_id, :item_key, :quantity, :use_day)"""
                    ),
                    {
                        "lot_id": int(item["inventory_lot_id"]),
                        "plan_id": plan.id,
                        "item_key": str(item["item_key"]),
                        "quantity": quantity,
                        "use_day": day,
                    },
                )

    def create_ending_lots(self, plan: MealPlanEntity) -> None:
        if plan.id is None or plan.start_date is None or plan.end_date is None:
            return
        for item in plan.plan_data.get("procurement", {}).get("purchase_items", []):
            quantity = float(item.get("carryover_quantity", 0))
            if quantity <= 0:
                continue
            eligible_splits = [
                split for split in item.get("storage_splits", [])
                if int(split.get("expiry_day", 0)) > len(plan.plan_data.get("days", []))
            ]
            if not eligible_splits:
                continue
            split = max(eligible_splits, key=lambda value: int(value["expiry_day"]))
            expiry = plan.start_date + timedelta(days=int(split["expiry_day"]) - 1)
            self._session.execute(
                text(
                    """INSERT INTO inventory_lots
                       (user_id, ingredient_id, quantity_remaining, unit,
                        purchase_increment, available_from, expires_on, storage_mode,
                        cost_basis_per_unit, source_plan_id, source_item_key, status)
                       VALUES (:user_id, :ingredient_id, :quantity, :unit,
                               :purchase_increment, :available_from, :expires_on, :storage_mode,
                               :cost_basis, :source_plan_id, :source_item_key, 'projected')
                       ON CONFLICT (source_plan_id, source_item_key) DO NOTHING"""
                ),
                {
                    "user_id": plan.user_id,
                    "ingredient_id": int(item["ingredient_id"]),
                    "quantity": quantity,
                    "unit": str(item["unit"]),
                    "purchase_increment": float(item["purchase_increment"]),
                    "available_from": plan.end_date + timedelta(days=1),
                    "expires_on": expiry,
                    "storage_mode": str(split["mode"]),
                    "cost_basis": float(item.get("price_per_default_unit", 0)),
                    "source_plan_id": plan.id,
                    "source_item_key": str(item["item_key"]),
                },
            )

    def release_plan(self, plan_id: int) -> None:
        dependent = self._session.execute(
            text(
                """SELECT COUNT(*) FROM inventory_reservations r
                   JOIN inventory_lots l ON l.id=r.inventory_lot_id
                   WHERE l.source_plan_id=:plan_id AND r.meal_plan_id<>:plan_id"""
            ),
            {"plan_id": plan_id},
        ).scalar_one()
        if int(dependent) > 0:
            raise ConflictError(
                "Không thể xóa thực đơn vì phần dư đang được thực đơn khác sử dụng."
            )
        reservations = self._session.execute(
            text(
                """SELECT inventory_lot_id, SUM(quantity) AS quantity
                   FROM inventory_reservations WHERE meal_plan_id=:plan_id
                   GROUP BY inventory_lot_id"""
            ),
            {"plan_id": plan_id},
        ).fetchall()
        for row in reservations:
            self._session.execute(
                text(
                    """UPDATE inventory_lots
                       SET quantity_remaining=quantity_remaining+:quantity,
                           status=CASE WHEN available_from <= CURRENT_DATE
                               THEN 'available' ELSE 'projected' END,
                           updated_at=NOW()
                       WHERE id=:id"""
                ),
                {"id": int(row.inventory_lot_id), "quantity": float(row.quantity)},
            )
        self._session.execute(
            text("DELETE FROM inventory_reservations WHERE meal_plan_id=:plan_id"),
            {"plan_id": plan_id},
        )
        self._session.execute(
            text("DELETE FROM inventory_lots WHERE source_plan_id=:plan_id"),
            {"plan_id": plan_id},
        )

    def list_lots(self, user_id: int) -> list[dict]:
        rows = self._session.execute(
            text(
                """SELECT l.id, l.ingredient_id, i.name, l.quantity_remaining, l.unit,
                          l.available_from, l.expires_on, l.storage_mode,
                          l.cost_basis_per_unit, l.source_plan_id, p.name AS source_plan_name,
                          CASE WHEN l.status='discarded' THEN 'discarded'
                               WHEN l.quantity_remaining <= 0 THEN 'consumed'
                               WHEN l.expires_on < CURRENT_DATE THEN 'expired'
                               WHEN l.available_from <= CURRENT_DATE THEN 'available'
                               ELSE 'projected' END AS status,
                          COALESCE(SUM(r.quantity), 0) AS reserved_quantity,
                          l.created_at
                   FROM inventory_lots l
                   JOIN ingredients i ON i.id=l.ingredient_id
                   LEFT JOIN meal_plans p ON p.id=l.source_plan_id
                   LEFT JOIN inventory_reservations r ON r.inventory_lot_id=l.id
                   WHERE l.user_id=:user_id
                   GROUP BY l.id, i.name, p.name
                   ORDER BY l.expires_on, i.name"""
            ),
            {"user_id": user_id},
        ).fetchall()
        return [dict(row._mapping) for row in rows]

    def update_lot(self, user_id: int, lot_id: int, changes: dict) -> dict:
        row = self._session.execute(
            text("SELECT * FROM inventory_lots WHERE id=:id AND user_id=:user_id FOR UPDATE"),
            {"id": lot_id, "user_id": user_id},
        ).first()
        if row is None:
            raise NotFoundError("Không tìm thấy lot kho")
        reserved = float(self._session.execute(
            text("SELECT COALESCE(SUM(quantity),0) FROM inventory_reservations WHERE inventory_lot_id=:id"),
            {"id": lot_id},
        ).scalar_one())
        if reserved > 0 and (
            changes.get("status") == "discarded"
            or changes.get("quantity_remaining") is not None
            and float(changes["quantity_remaining"]) < float(row.quantity_remaining)
        ):
            raise ConflictError(
                "Lot đang được thực đơn khác giữ chỗ; hãy xóa hoặc tạo lại thực đơn đó trước."
            )
        expires_on = changes.get("expires_on", row.expires_on)
        if expires_on < row.available_from:
            raise ValidationAppError("Hạn dùng không thể trước ngày lot khả dụng")
        self._session.execute(
            text(
                """UPDATE inventory_lots SET
                     quantity_remaining=:quantity,
                     expires_on=:expires_on,
                     storage_mode=:storage_mode,
                     status=:status,
                     updated_at=NOW()
                   WHERE id=:id"""
            ),
            {
                "id": lot_id,
                "quantity": changes.get("quantity_remaining", float(row.quantity_remaining)),
                "expires_on": expires_on,
                "storage_mode": changes.get("storage_mode", str(row.storage_mode)),
                "status": changes.get("status", str(row.status)),
            },
        )
        self._session.flush()
        return next(item for item in self.list_lots(user_id) if int(item["id"]) == lot_id)

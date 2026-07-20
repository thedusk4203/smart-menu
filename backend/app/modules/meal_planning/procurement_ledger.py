from __future__ import annotations

from typing import Any

from app.modules.meal_planning.domain import PlanRequest


def build_daily_ledger(
    request: PlanRequest,
    supply_items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Build an auditable opening + purchase - use - expiry = closing ledger."""
    balances = {item["item_key"]: 0.0 for item in supply_items}
    result: list[dict[str, Any]] = []
    for day in range(1, request.days + 1):
        rows: list[dict[str, Any]] = []
        for item in supply_items:
            key = item["item_key"]
            source_kind = item["source_kind"]
            available_day = int(item["_available_day"])
            if source_kind == "inventory" and available_day == day:
                balances[key] += float(item["starting_quantity"])
            opening = round(balances[key], 2)
            purchase = 0.0
            if source_kind == "purchase" and available_day == day:
                purchase = float(item["purchase_quantity"])
                balances[key] += purchase
            allocations = [
                dict(allocation)
                for allocation in item["allocations"]
                if int(allocation["day"]) == day
            ]
            used = round(sum(float(value["quantity"]) for value in allocations), 2)
            balances[key] = max(0.0, round(balances[key] - used, 2))
            expiry_days = [
                int(split["expiry_day"])
                for split in item["storage_splits"]
                if float(split["quantity"]) > 0
            ]
            final_expiry = max(expiry_days) if expiry_days else request.days + 1
            expired = 0.0
            if final_expiry == day and balances[key] > 0:
                expired = round(balances[key], 2)
                balances[key] = 0.0
            closing = round(balances[key], 2)
            if opening <= 0 and purchase <= 0 and used <= 0 and expired <= 0 and closing <= 0:
                continue
            rows.append(
                {
                    "item_key": key,
                    "source_kind": source_kind,
                    "inventory_lot_id": item.get("inventory_lot_id"),
                    "ingredient_id": item["ingredient_id"],
                    "name": item["name"],
                    "unit": item["unit"],
                    "opening_quantity": opening,
                    "purchase_quantity": round(purchase, 2),
                    "usage_quantity": used,
                    "expired_quantity": expired,
                    "closing_quantity": closing,
                    "unit_value": item["price_per_default_unit"],
                    "purchase_cost": item["purchase_cost"] if purchase > 0 else 0,
                    "allocations": allocations,
                }
            )
        result.append(
            {
                "day": day,
                "items": rows,
                "totals": {
                    "opening_value": round(
                        sum(row["opening_quantity"] * row["unit_value"] for row in rows)
                    ),
                    "purchase_cost": round(sum(row["purchase_cost"] for row in rows)),
                    "usage_value": round(
                        sum(row["usage_quantity"] * row["unit_value"] for row in rows)
                    ),
                    "expired_value": round(
                        sum(row["expired_quantity"] * row["unit_value"] for row in rows)
                    ),
                    "closing_value": round(
                        sum(row["closing_quantity"] * row["unit_value"] for row in rows)
                    ),
                },
            }
        )
    return result

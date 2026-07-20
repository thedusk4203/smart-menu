from __future__ import annotations

from app.modules.meal_planning.domain import MealPlanEntity
from app.modules.shopping_lists.exceptions import (
    ShoppingListDayNotFoundError,
    ShoppingListScopeError,
    UnsupportedShoppingPlanError,
)
from app.modules.shopping_lists.ports import (
    ShoppingListUnitOfWorkPort,
    ShoppingShareRepositoryPort,
)
from app.modules.shopping_lists.schemas import ShoppingListResponse


class BuildShoppingListUseCase:
    """Chiếu snapshot meal-plan V3 ledger thành danh sách mua sắm."""

    def __init__(self, unit_of_work: ShoppingListUnitOfWorkPort | None = None) -> None:
        self._unit_of_work = unit_of_work

    def execute(
        self,
        plan: MealPlanEntity,
        day: int | None = None,
        scope: str | None = None,
    ) -> ShoppingListResponse:
        if int(plan.plan_data.get("schema_version", 0)) != 3:
            raise UnsupportedShoppingPlanError()
        procurement = plan.plan_data.get("procurement", {})
        if int(procurement.get("ledger_version", 0)) != 2:
            raise UnsupportedShoppingPlanError()

        selected_day = self._selected_day(plan.plan_data, day)
        resolved_scope = scope or ("usage_day" if day is not None else "all")
        if resolved_scope not in {"all", "purchase_day", "usage_day"}:
            raise ShoppingListScopeError()
        if resolved_scope != "all" and day is None:
            raise ShoppingListScopeError("Phạm vi theo ngày cần có query day")
        return self._from_v3_plan(plan, day, resolved_scope, selected_day)

    def _from_v3_plan(
        self,
        plan: MealPlanEntity,
        day: int | None,
        scope: str,
        selected_day: dict | None,
    ) -> ShoppingListResponse:
        procurement = plan.plan_data["procurement"]
        raw_purchase = list(procurement.get("purchase_items", []))
        raw_pantry = list(procurement.get("pantry_checks", []))
        all_ledger = list(procurement.get("daily_ledger", []))
        visible_ledger = all_ledger if day is None else [
            value for value in all_ledger if int(value.get("day", 0)) == day
        ]

        materialized = [
            {
                **raw,
                "quantity": float(raw.get("purchase_quantity", 0)),
                "estimated_cost": float(raw.get("purchase_cost", 0)),
                "item_kind": "purchase",
                "scheduled_day": int(raw.get("purchase_day", 0)) or None,
                "is_purchased": False,
            }
            for raw in raw_purchase
        ]
        materialized.extend(
            {
                **raw,
                "quantity": float(raw.get("quantity", 0)),
                "estimated_cost": 0.0,
                "item_kind": "pantry",
                "scheduled_day": None,
                "is_purchased": False,
            }
            for raw in raw_pantry
        )
        persisted = self._materialize(plan.id, materialized) if plan.id else []
        persisted_by_key = {str(item.get("item_key")): item for item in persisted}

        def with_state(item: dict) -> dict:
            saved = persisted_by_key.get(str(item.get("item_key")), {})
            return {
                **item,
                "id": saved.get("id"),
                "is_purchased": bool(saved.get("is_purchased", False)),
            }

        purchase_items = [
            with_state(item)
            for item in materialized
            if item["item_kind"] == "purchase"
            and (day is None or int(item.get("scheduled_day") or 0) == day)
        ]
        pantry_ids = self._pantry_ids_for_day(plan.plan_data, day) if day else None
        pantry_items = [
            with_state(item)
            for item in materialized
            if item["item_kind"] == "pantry"
            and (pantry_ids is None or int(item["ingredient_id"]) in pantry_ids)
        ]
        carryover_usage: list[dict] = []
        if day is not None:
            for ledger_day in visible_ledger:
                for row in ledger_day.get("items", []):
                    for allocation in row.get("allocations", []):
                        if (
                            row.get("source_kind") == "inventory"
                            or float(row.get("opening_quantity", 0)) > 0
                        ):
                            carryover_usage.append(
                                {
                                    "ingredient_id": int(row["ingredient_id"]),
                                    "name": str(row["name"]),
                                    "quantity": float(allocation["quantity"]),
                                    "unit": str(row["unit"]),
                                    "purchase_day": max(1, day - 1),
                                    "use_day": day,
                                    "storage_mode": str(
                                        allocation.get("storage_mode") or "stored"
                                    ),
                                    "expiry_day": int(allocation.get("expiry_day") or day),
                                    "dish_name": allocation.get("dish_name"),
                                }
                            )
        leftovers = [
            {
                "ingredient_id": int(row["ingredient_id"]),
                "name": str(row["name"]),
                "quantity": float(row["closing_quantity"]),
                "unit": str(row["unit"]),
                "purchase_day": day or int(ledger_day["day"]),
                "status": "closing_stock",
            }
            for ledger_day in visible_ledger[-1:]
            for row in ledger_day.get("items", [])
            if float(row.get("closing_quantity", 0)) > 0
        ]
        summary = dict(plan.plan_data.get("cost_summary", {}))
        summary["visible_purchase_cost"] = round(
            sum(float(item["purchase_cost"]) for item in purchase_items)
        )
        summary["shopping_days"] = len(procurement.get("shopping_days", []))
        adapter_items = [*purchase_items, *pantry_items]
        return ShoppingListResponse(
            plan_id=plan.id or 0,
            plan_name=plan.name,
            day=day,
            date=selected_day.get("date") if selected_day else None,
            scope=scope,
            items=adapter_items,
            total_estimated_cost=round(
                sum(float(item["estimated_cost"]) for item in adapter_items)
            ),
            purchase_items=purchase_items,
            pantry_checks=pantry_items,
            carryover_usage=carryover_usage,
            leftovers=leftovers,
            daily_ledger=visible_ledger,
            summary=summary,
            warnings=[
                {
                    "code": str(value["code"]),
                    "message": str(value.get("message") or value["code"]),
                }
                for value in plan.plan_data.get("warnings", [])
                if isinstance(value, dict) and value.get("code")
            ],
        )

    @staticmethod
    def _pantry_ids_for_day(plan_data: dict, day: int) -> set[int]:
        selected = BuildShoppingListUseCase._selected_day(plan_data, day)
        return {
            int(ingredient["ingredient_id"])
            for meal in (selected or {}).get("meals", [])
            for dish in meal.get("dishes", [])
            for ingredient in dish.get("ingredients", [])
            if ingredient.get("purchase_mode") == "pantry"
        }

    @staticmethod
    def _selected_day(plan_data: dict, day: int | None) -> dict | None:
        if day is None:
            return None
        for index, plan_day in enumerate(plan_data.get("days", []), start=1):
            if int(plan_day.get("day", index)) == day:
                return plan_day
        raise ShoppingListDayNotFoundError(day)

    def _materialize(self, plan_id: int, items: list[dict]) -> list[dict]:
        if self._unit_of_work is None:
            return []
        try:
            persisted = self._unit_of_work.shopping_lists.ensure_items(plan_id, items)
            self._unit_of_work.commit()
            return persisted
        except Exception:
            self._unit_of_work.rollback()
            raise


class UpdateShoppingItemUseCase:
    def __init__(self, unit_of_work: ShoppingListUnitOfWorkPort) -> None:
        self._unit_of_work = unit_of_work

    def execute(self, plan_id: int, item_id: int, purchased: bool) -> dict | None:
        try:
            result = self._unit_of_work.shopping_lists.set_purchased(
                plan_id, item_id, purchased
            )
            self._unit_of_work.commit()
            return result
        except Exception:
            self._unit_of_work.rollback()
            raise


class GetOrCreateShoppingShareUseCase:
    def __init__(self, unit_of_work: ShoppingListUnitOfWorkPort) -> None:
        self._unit_of_work = unit_of_work

    def execute(self, plan_id: int) -> dict:
        try:
            result = self._unit_of_work.shares.get_or_create(plan_id)
            self._unit_of_work.commit()
            return result
        except Exception:
            self._unit_of_work.rollback()
            raise


class GetActiveShoppingShareUseCase:
    def __init__(self, repository: ShoppingShareRepositoryPort) -> None:
        self._repository = repository

    def execute(self, share_id: str) -> dict | None:
        return self._repository.get_active(share_id)


class RevokeShoppingShareUseCase:
    def __init__(self, unit_of_work: ShoppingListUnitOfWorkPort) -> None:
        self._unit_of_work = unit_of_work

    def execute(self, plan_id: int) -> None:
        try:
            self._unit_of_work.shares.revoke(plan_id)
            self._unit_of_work.commit()
        except Exception:
            self._unit_of_work.rollback()
            raise

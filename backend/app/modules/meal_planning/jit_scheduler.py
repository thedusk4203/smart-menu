"""Deterministic just-in-time procurement scheduling for selected dishes."""
from __future__ import annotations

import math
from typing import Any

from app.modules.meal_planning.domain import (
    DishIngredientSnapshot,
    PlanRequest,
)


_EPSILON = 1e-8


class JitProcurementScheduler:
    """Build a canonical FEFO/JIT supply schedule independent of CP-SAT phases.

    CP-SAT still chooses dishes with purchase cost in its objective. Once the
    dishes are fixed, this scheduler rebuilds their physical supply flow so a
    purchase is created only on a day that immediately consumes some of it.
    """

    def schedule(
        self,
        request: PlanRequest,
        ingredients: dict[int, DishIngredientSnapshot],
        occurrences: dict[int, list[dict[str, Any]]],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        inventory_items = self._inventory_items(request, ingredients)
        purchase_items: list[dict[str, Any]] = []
        purchases_by_key: dict[tuple[int, int], dict[str, Any]] = {}

        for ingredient_id, ingredient_occurrences in occurrences.items():
            ingredient = ingredients[ingredient_id]
            if ingredient.purchase_mode != "regular":
                continue

            inventory_for_ingredient = sorted(
                (
                    item
                    for item in inventory_items
                    if int(item["ingredient_id"]) == ingredient_id
                ),
                key=lambda item: (
                    int(item["_fixed_expiry_day"]),
                    int(item["inventory_lot_id"]),
                ),
            )
            purchases_for_ingredient: list[dict[str, Any]] = []

            for occurrence in sorted(
                ingredient_occurrences,
                key=lambda value: (int(value["day"]), int(value["sequence"])),
            ):
                needed = float(occurrence["base_quantity"])
                use_day = int(occurrence["day"])

                # Existing inventory is always consumed before any purchased
                # carry-over, with FEFO ordering inside the inventory pool.
                for item in inventory_for_ingredient:
                    if needed <= _EPSILON:
                        break
                    if not (
                        int(item["_available_day"])
                        <= use_day
                        <= int(item["_fixed_expiry_day"])
                    ):
                        continue
                    needed = self._allocate(
                        item, occurrence, needed, ingredient
                    )

                # Reuse earlier purchase remainders while they are still
                # storable; buying again is the last resort.
                for item in sorted(
                    purchases_for_ingredient,
                    key=lambda value: (
                        int(value["purchase_day"])
                        + ingredient.max_shelf_life_days,
                        int(value["purchase_day"]),
                    ),
                ):
                    if needed <= _EPSILON:
                        break
                    if use_day - int(item["purchase_day"]) > ingredient.max_shelf_life_days:
                        continue
                    needed = self._allocate(
                        item, occurrence, needed, ingredient
                    )

                if needed <= _EPSILON:
                    continue

                # A deficit is purchased on its use day. The newly bought lot
                # therefore always has a positive same-day allocation.
                key = (ingredient_id, use_day)
                item = purchases_by_key.get(key)
                if item is None:
                    item = self._new_purchase_item(ingredient, use_day)
                    purchases_by_key[key] = item
                    purchase_items.append(item)
                    purchases_for_ingredient.append(item)
                self._add_purchase_capacity(item, ingredient, needed)
                remaining = self._allocate(item, occurrence, needed, ingredient)
                if remaining > 1e-6:
                    raise ValueError(
                        f"JIT không cấp đủ nguyên liệu {ingredient.name} ngày {use_day}"
                    )

        purchase_items.sort(
            key=lambda item: (int(item["purchase_day"]), int(item["ingredient_id"]))
        )
        inventory_items.sort(
            key=lambda item: (
                int(item["_fixed_expiry_day"]),
                int(item["inventory_lot_id"]),
            )
        )
        return purchase_items, inventory_items

    @staticmethod
    def _inventory_items(
        request: PlanRequest,
        ingredients: dict[int, DishIngredientSnapshot],
    ) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for lot in request.inventory_lots:
            ingredient = ingredients.get(lot.ingredient_id)
            if (
                ingredient is None
                or ingredient.purchase_mode != "regular"
                or lot.unit != ingredient.unit
                or lot.quantity <= _EPSILON
            ):
                continue
            result.append({
                "item_key": f"inventory:{lot.lot_id}",
                "source_kind": "inventory",
                "inventory_lot_id": lot.lot_id,
                "ingredient_id": lot.ingredient_id,
                "name": lot.name,
                "unit": lot.unit,
                "purchase_day": lot.available_day,
                "available_day": lot.available_day,
                "purchase_increment": lot.purchase_increment,
                "starting_quantity": round(lot.quantity, 2),
                "purchase_quantity": 0.0,
                "purchase_cost": 0,
                "price_per_default_unit": lot.cost_basis_per_unit,
                "price_source": "inventory_cost_basis",
                "price_recorded_at": None,
                "allocations": [],
                "storage_splits": [],
                "remaining_quantity": round(lot.quantity, 2),
                "expired_waste_quantity": 0.0,
                "carryover_quantity": 0.0,
                "_available_day": lot.available_day,
                "_fixed_expiry_day": lot.expiry_day,
                "_fixed_storage_mode": lot.storage_mode,
            })
        return result

    @staticmethod
    def _new_purchase_item(
        ingredient: DishIngredientSnapshot,
        purchase_day: int,
    ) -> dict[str, Any]:
        return {
            "item_key": f"purchase:{ingredient.ingredient_id}:{purchase_day}",
            "source_kind": "purchase",
            "ingredient_id": ingredient.ingredient_id,
            "name": ingredient.name,
            "unit": ingredient.unit,
            "purchase_day": purchase_day,
            "purchase_increment": float(ingredient.purchase_increment),
            "block_count": 0,
            "purchase_quantity": 0.0,
            "purchase_cost": 0,
            "price_per_default_unit": ingredient.price_per_default_unit,
            "price_source": ingredient.price_source,
            "price_recorded_at": ingredient.price_recorded_at,
            "allocations": [],
            "storage_splits": [],
            "remaining_quantity": 0.0,
            "expired_waste_quantity": 0.0,
            "carryover_quantity": 0.0,
            "_available_day": purchase_day,
        }

    @staticmethod
    def _add_purchase_capacity(
        item: dict[str, Any],
        ingredient: DishIngredientSnapshot,
        deficit: float,
    ) -> None:
        increment = float(ingredient.purchase_increment)
        blocks = max(1, math.ceil((deficit - _EPSILON) / increment))
        quantity = blocks * increment
        block_price = int(
            math.ceil(increment * float(ingredient.price_per_default_unit) - 1e-9)
        )
        item["block_count"] = int(item["block_count"]) + blocks
        item["purchase_quantity"] = round(
            float(item["purchase_quantity"]) + quantity, 2
        )
        item["purchase_cost"] = int(item["purchase_cost"]) + block_price * blocks
        item["remaining_quantity"] = round(
            float(item["remaining_quantity"]) + quantity, 2
        )

    def _allocate(
        self,
        item: dict[str, Any],
        occurrence: dict[str, Any],
        needed: float,
        ingredient: DishIngredientSnapshot,
    ) -> float:
        available = float(item["remaining_quantity"])
        if available <= _EPSILON:
            return needed
        quantity = min(available, needed)
        use_day = int(occurrence["day"])
        if item["source_kind"] == "inventory":
            storage_mode = str(item["_fixed_storage_mode"])
            expiry_day = int(item["_fixed_expiry_day"])
        else:
            storage_mode, expiry_day = self._storage_for(
                ingredient,
                use_day - int(item["purchase_day"]),
                int(item["purchase_day"]),
            )
        item["allocations"].append({
            "day": use_day,
            "slot": occurrence["slot"],
            "dish_id": occurrence["dish_id"],
            "dish_name": occurrence["dish_name"],
            "quantity": round(quantity, 2),
            "kind": "base",
            "storage_mode": storage_mode,
            "expiry_day": expiry_day,
            "sequence": occurrence["sequence"],
        })
        item["remaining_quantity"] = round(available - quantity, 2)
        return max(0.0, round(needed - quantity, 2))

    @staticmethod
    def _storage_for(
        ingredient: DishIngredientSnapshot,
        delta_days: int,
        purchase_day: int,
    ) -> tuple[str, int]:
        options = (
            ("room", ingredient.room_shelf_life_days),
            ("fridge", ingredient.fridge_shelf_life_days),
            ("freezer", ingredient.freezer_shelf_life_days),
        )
        for mode, shelf_life in options:
            if shelf_life is not None and shelf_life >= delta_days:
                return mode, purchase_day + shelf_life
        if delta_days == 0:
            return "same_day", purchase_day
        raise ValueError(f"Không có phương thức bảo quản hợp lệ cho {ingredient.name}")

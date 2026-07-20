from __future__ import annotations

from datetime import date as Date
from datetime import datetime

from typing import Literal

from pydantic import BaseModel, Field


class ShoppingListItem(BaseModel):
    id: int | None = None
    ingredient_id: int
    name: str
    quantity: float
    unit: str
    estimated_cost: float
    is_purchased: bool = False
    item_key: str | None = None
    item_kind: Literal["purchase", "pantry"] = "purchase"
    scheduled_day: int | None = None


class PurchaseItem(ShoppingListItem):
    required_quantity: float
    purchase_quantity: float
    purchase_cost: float
    purchase_increment: float
    block_count: int
    remaining_quantity: float = 0
    expired_waste_quantity: float = 0
    carryover_quantity: float = 0
    storage_splits: list[dict] = Field(default_factory=list)


class PantryCheck(ShoppingListItem):
    item_kind: Literal["pantry"] = "pantry"


class CarryoverUsage(BaseModel):
    ingredient_id: int
    name: str
    quantity: float
    unit: str
    purchase_day: int
    use_day: int
    storage_mode: str
    expiry_day: int
    dish_name: str | None = None


class LeftoverItem(BaseModel):
    ingredient_id: int
    name: str
    quantity: float
    unit: str
    purchase_day: int
    status: Literal["carryover", "closing_stock", "expired_waste"]


class DailyLedgerItem(BaseModel):
    item_key: str
    source_kind: Literal["inventory", "purchase"]
    inventory_lot_id: int | None = None
    ingredient_id: int
    name: str
    unit: str
    opening_quantity: float
    purchase_quantity: float
    usage_quantity: float
    expired_quantity: float
    closing_quantity: float
    unit_value: float
    purchase_cost: float
    allocations: list[dict] = Field(default_factory=list)


class DailyLedgerDay(BaseModel):
    day: int
    items: list[DailyLedgerItem] = Field(default_factory=list)
    totals: dict[str, float | int] = Field(default_factory=dict)


class ShoppingListWarning(BaseModel):
    code: str
    message: str


class ShoppingListResponse(BaseModel):
    plan_id: int
    plan_name: str | None = None
    day: int | None = None
    date: Date | None = None
    schema_version: Literal[3] = 3
    shopping_schema_version: Literal[3] = 3
    scope: Literal["all", "purchase_day", "usage_day"] = "all"
    items: list[ShoppingListItem] = Field(default_factory=list)
    total_estimated_cost: float
    purchase_items: list[PurchaseItem] = Field(default_factory=list)
    pantry_checks: list[PantryCheck] = Field(default_factory=list)
    carryover_usage: list[CarryoverUsage] = Field(default_factory=list)
    leftovers: list[LeftoverItem] = Field(default_factory=list)
    daily_ledger: list[DailyLedgerDay] = Field(default_factory=list)
    summary: dict[str, float | int] = Field(default_factory=dict)
    warnings: list[ShoppingListWarning] = Field(default_factory=list)


class PurchaseUpdate(BaseModel):
    is_purchased: bool


class BulkPurchaseUpdate(BaseModel):
    item_ids: list[int] = Field(min_length=1, max_length=200)
    is_purchased: bool


class ShoppingShareResponse(BaseModel):
    token: str
    expires_at: datetime
    day: int | None = None
    scope: Literal["all", "purchase_day", "usage_day"] = "all"


class PublicShoppingListResponse(ShoppingListResponse):
    expires_at: datetime

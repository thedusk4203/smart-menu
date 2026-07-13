from __future__ import annotations

from datetime import date as Date
from datetime import datetime

from pydantic import BaseModel, Field


class ShoppingListItem(BaseModel):
    id: int | None = None
    ingredient_id: int
    name: str
    quantity: float
    unit: str
    estimated_cost: float
    is_purchased: bool = False


class ShoppingListWarning(BaseModel):
    code: str
    message: str


class ShoppingListResponse(BaseModel):
    plan_id: int
    plan_name: str | None = None
    day: int | None = None
    date: Date | None = None
    schema_version: int
    items: list[ShoppingListItem] = Field(default_factory=list)
    total_estimated_cost: float
    warnings: list[ShoppingListWarning] = Field(default_factory=list)


class PurchaseUpdate(BaseModel):
    is_purchased: bool


class ShoppingShareResponse(BaseModel):
    token: str
    expires_at: datetime
    day: int | None = None


class PublicShoppingListResponse(ShoppingListResponse):
    expires_at: datetime

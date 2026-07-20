from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


InventoryStatus = Literal["projected", "available", "consumed", "expired", "discarded"]
StorageMode = Literal["room", "fridge", "freezer", "same_day"]


class InventoryLotResponse(BaseModel):
    id: int
    ingredient_id: int
    name: str
    quantity_remaining: float
    unit: str
    available_from: date
    expires_on: date
    storage_mode: StorageMode
    cost_basis_per_unit: float
    source_plan_id: int | None = None
    source_plan_name: str | None = None
    status: InventoryStatus
    reserved_quantity: float = 0
    created_at: datetime


class InventoryLotUpdate(BaseModel):
    quantity_remaining: float | None = Field(default=None, ge=0)
    expires_on: date | None = None
    storage_mode: StorageMode | None = None
    status: Literal["available", "discarded"] | None = None

    @model_validator(mode="after")
    def has_change(self) -> "InventoryLotUpdate":
        if all(value is None for value in (
            self.quantity_remaining, self.expires_on, self.storage_mode, self.status
        )):
            raise ValueError("Cần ít nhất một thay đổi cho lot kho")
        return self

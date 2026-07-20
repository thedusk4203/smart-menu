from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any


@dataclass(frozen=True)
class InventoryLotSnapshot:
    """Lot kho khả dụng được chuẩn hóa tương đối theo ngày bắt đầu plan."""

    lot_id: int
    ingredient_id: int
    name: str
    quantity: float
    unit: str
    purchase_increment: float
    available_day: int
    expiry_day: int
    storage_mode: str
    cost_basis_per_unit: float = 0.0


@dataclass(frozen=True)
class PersistedPlanInventory:
    """Dữ liệu tối thiểu inventory cần sau khi meal plan đã được lưu."""

    plan_id: int
    user_id: int
    start_date: date
    end_date: date
    plan_data: dict[str, Any]

from __future__ import annotations

from app.core.exceptions import ValidationAppError


class ShoppingListDayNotFoundError(ValidationAppError):
    def __init__(self, day: int) -> None:
        super().__init__(f"Ngày {day} không tồn tại trong thực đơn đã chọn")

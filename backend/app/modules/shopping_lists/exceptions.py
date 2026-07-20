from __future__ import annotations

from app.core.exceptions import ValidationAppError


class ShoppingListDayNotFoundError(ValidationAppError):
    def __init__(self, day: int) -> None:
        super().__init__(f"Ngày {day} không tồn tại trong thực đơn đã chọn")


class ShoppingListScopeError(ValidationAppError):
    def __init__(self, message: str = "Phạm vi danh sách mua không hợp lệ") -> None:
        super().__init__(message)


class UnsupportedShoppingPlanError(ValidationAppError):
    def __init__(self) -> None:
        super().__init__("Thực đơn cũ không còn được hỗ trợ; hãy tạo lại bằng Planner V3.")

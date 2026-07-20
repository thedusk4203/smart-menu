from __future__ import annotations

from app.core.exceptions import ValidationAppError


class ShoppingListDayNotFoundError(ValidationAppError):
    def __init__(self, day: int) -> None:
        super().__init__(
            f"Ngày {day} không tồn tại trong thực đơn đã chọn",
            code="SHOPPING_DAY_NOT_FOUND",
            user_message="Ngày đã chọn không còn trong thực đơn. Hãy chọn ngày khác.",
            details={"day": day},
        )


class ShoppingListScopeError(ValidationAppError):
    def __init__(self, message: str = "Phạm vi danh sách mua không hợp lệ") -> None:
        super().__init__(
            message,
            code="SHOPPING_SCOPE_INVALID",
            user_message="Phạm vi danh sách đi chợ chưa hợp lệ. Hãy chọn lại thực đơn hoặc ngày.",
        )


class UnsupportedShoppingPlanError(ValidationAppError):
    def __init__(self) -> None:
        super().__init__(
            "Thực đơn cũ không còn được hỗ trợ; hãy tạo lại bằng Planner V3.",
            code="SHOPPING_PLAN_UNSUPPORTED",
            user_message="Thực đơn này được tạo bằng phiên bản cũ. Hãy tạo thực đơn mới để lập danh sách đi chợ.",
        )

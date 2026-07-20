from __future__ import annotations

from app.core.exceptions import NotFoundError, ValidationAppError


class MealPlanNotFoundError(NotFoundError):
    def __init__(self, plan_id: int) -> None:
        super().__init__(
            f"Không tìm thấy thực đơn id={plan_id}",
            code="MEAL_PLAN_NOT_FOUND",
            user_message="Không tìm thấy thực đơn này. Thực đơn có thể đã bị xóa.",
            details={"plan_id": plan_id},
        )


class IncompleteProfileError(ValidationAppError):
    """Hồ sơ thiếu trường bắt buộc để tính mục tiêu dinh dưỡng (giới tính,
    tuổi, chiều cao, cân nặng). Chặn sớm."""

    def __init__(self, missing: list[str]) -> None:
        joined = ", ".join(missing)
        super().__init__(
            f"Hồ sơ chưa đủ thông tin để lập thực đơn (thiếu: {joined}). "
            "Vui lòng cập nhật hồ sơ.",
            code="PROFILE_INCOMPLETE",
            user_message="Hồ sơ còn thiếu thông tin để tạo thực đơn.",
            details={"missing_fields": missing},
            fields={field: "Vui lòng bổ sung thông tin này." for field in missing},
        )


class InfeasibleNutritionError(ValidationAppError):
    """Mục tiêu dinh dưỡng tính ra không khả thi (ví dụ calo < ngưỡng an toàn).
    Không thể sinh thực đơn an toàn -> báo rõ thay vì lập thực đơn theo mục
    tiêu vô nghĩa."""

    def __init__(self, reasons: list[str]) -> None:
        detail = "; ".join(reasons) if reasons else "mục tiêu calo quá thấp"
        super().__init__(
            f"Mục tiêu dinh dưỡng không khả thi: {detail}",
            code="NUTRITION_TARGET_INFEASIBLE",
            user_message="Mục tiêu dinh dưỡng hiện tại chưa phù hợp để tạo thực đơn an toàn.",
            details={"reasons": reasons},
        )


class InvalidMealSelectionError(ValidationAppError):
    """Khi LƯU thực đơn: client gửi dish không hợp lệ hoặc ghép sai cấu trúc."""

    def __init__(self, detail: str) -> None:
        super().__init__(
            f"Lựa chọn thực đơn không hợp lệ: {detail}",
            code="MEAL_SELECTION_INVALID",
            user_message="Thực đơn đã thay đổi và chưa thể lưu. Hãy tạo lại phương án mới.",
        )

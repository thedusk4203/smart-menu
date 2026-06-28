# File: backend/app/modules/meal_planning/exceptions.py
from __future__ import annotations

from app.core.exceptions import NotFoundError, ValidationAppError


class MealPlanNotFoundError(NotFoundError):
    def __init__(self, plan_id: int) -> None:
        super().__init__(f"Không tìm thấy thực đơn id={plan_id}")


class IncompleteProfileError(ValidationAppError):
    """Hồ sơ thiếu trường bắt buộc để tính mục tiêu dinh dưỡng (giới tính,
    tuổi, chiều cao, cân nặng). Chặn sớm để không vỡ thành lỗi 500 mơ hồ ở
    NutritionCalculator (review D-02)."""

    def __init__(self, missing: list[str]) -> None:
        joined = ", ".join(missing)
        super().__init__(
            f"Hồ sơ chưa đủ thông tin để lập thực đơn (thiếu: {joined}). "
            "Vui lòng cập nhật hồ sơ."
        )


class InfeasibleNutritionError(ValidationAppError):
    """Mục tiêu dinh dưỡng tính ra không khả thi (ví dụ calo < ngưỡng an toàn).
    Không thể sinh thực đơn an toàn -> báo rõ thay vì lập thực đơn theo mục
    tiêu vô nghĩa (review D-02)."""

    def __init__(self, reasons: list[str]) -> None:
        detail = "; ".join(reasons) if reasons else "mục tiêu calo quá thấp"
        super().__init__(f"Mục tiêu dinh dưỡng không khả thi: {detail}")

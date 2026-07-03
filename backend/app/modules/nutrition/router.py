# File: backend/app/modules/nutrition/router.py
# HTTP surface cho module nutrition. Trước đây module này đã tính toán đầy đủ
# (NutritionCalculator) nhưng CHƯA có router nên frontend không gọi được —
# đây là phần bổ sung để lộ nhu cầu dinh dưỡng ra API.
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies import get_calculate_nutrition_target_use_case
from app.modules.nutrition.schemas import NutritionProfileInput, NutritionTargetResponse
from app.modules.nutrition.use_cases import CalculateNutritionTargetUseCase

router = APIRouter(prefix="/api/nutrition", tags=["nutrition"])


@router.post("/target", response_model=NutritionTargetResponse)
def calculate_target(
    data: NutritionProfileInput,
    use_case: CalculateNutritionTargetUseCase = Depends(get_calculate_nutrition_target_use_case),
):
    """Tính nhu cầu dinh dưỡng/ngày từ thông tin hồ sơ (không cần đăng nhập,
    không đọc DB): BMR, TDEE, calo mục tiêu, macro (đạm/béo/tinh bột) và các
    cảnh báo an toàn. Thuần deterministic — dùng cho trang Hồ sơ để người dùng
    xem trước nhu cầu khi nhập chiều cao/cân nặng/mục tiêu.
    """
    return use_case.execute(data)

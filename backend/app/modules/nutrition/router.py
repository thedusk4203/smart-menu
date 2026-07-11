
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

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True)
class MealPlanEntity:
    id: int | None
    user_id: int
    name: str = "Thực đơn tuần"
    start_date: date | None = None  # None khi vừa sinh (chưa lưu); set khi lưu
    end_date: date | None = None
    budget_limit: float | None = None
    total_cost: float = 0
    total_calories: float = 0
    plan_data: dict = field(default_factory=dict)


@dataclass(frozen=True)
class PlanRequest:
    """Yêu cầu tạo thực đơn đã chuẩn hóa (từ form hoặc AI parser).

    Mục tiêu dinh dưỡng (target_*) lấy từ CalculateNutritionTargetUseCase;
    danh sách loại trừ gộp cả dị ứng (allergy) và không ăn (dislike)."""
    user_id: int
    days: int                            # Số ngày (MVP mặc định: 7)
    meals_per_day: int                   # Số bữa/ngày (2 hoặc 3)
    budget_limit: float | None           # Ngân sách cả kỳ (đồng); None = không giới hạn
    target_calories: float               # Mục tiêu/ngày
    target_protein_g: float
    target_fat_g: float
    target_carb_g: float
    excluded_ingredient_ids: list[int] = field(default_factory=list)  # Dị ứng + không ăn
    preferred_tags: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class MealCandidate:
    """Món ăn hợp lệ để chọn vào thực đơn — đọc tổng hợp từ v_meals_full
    kèm danh sách ingredient_ids (để kiểm tra loại trừ + tái sử dụng)."""
    meal_id: int
    name: str
    meal_type: str                       # breakfast/lunch/dinner
    total_calories: float
    total_protein_g: float
    total_fat_g: float
    total_carb_g: float
    estimated_cost: float
    ingredient_ids: list[int] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ValidationResult:
    """Kết quả kiểm tra ràng buộc cho toàn bộ thực đơn (SRS §5.4).

    status:
      - "valid"                : đạt mọi ràng buộc cứng, không cảnh báo
      - "valid_with_warnings"  : đạt ràng buộc cứng nhưng có cảnh báo mềm
      - "infeasible"           : không thể lập thực đơn hợp lệ"""
    status: str
    hard_violations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    infeasible_reasons: list[str] = field(default_factory=list)

    @property
    def is_feasible(self) -> bool:
        return self.status != "infeasible"

@dataclass(frozen=True)
class PlannedMeal:
    """Một món đã xếp vào một slot bữa trong ngày."""
    meal_id: int
    name: str
    meal_type: str          # breakfast/lunch/dinner
    calories: float
    protein_g: float
    fat_g: float
    carb_g: float
    cost: float


@dataclass(frozen=True)
class PlannedDay:
    """Một ngày trong thực đơn: danh sách bữa + tổng hợp calo/chi phí ngày."""
    day: int                # 1-based
    date: str | None        # ISO date hoặc None nếu chưa gán ngày bắt đầu
    meals: list[PlannedMeal]
    day_calories: float
    day_cost: float

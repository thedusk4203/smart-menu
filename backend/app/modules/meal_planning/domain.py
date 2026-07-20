from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime

from app.shared.enums import CookingMethod, DishType, MealType


@dataclass(frozen=True)
class DishIngredientSnapshot:
    """Nguyên liệu tại thời điểm candidate được đọc cho Planner V3."""

    ingredient_id: int
    name: str
    quantity: float
    unit: str
    estimated_cost: float
    purchase_mode: str = "regular"
    purchase_increment: float | None = None
    price_per_default_unit: float | None = None
    price_source: str | None = None
    price_recorded_at: str | None = None
    grams_per_unit: float = 1.0
    calories_per_100g: float = 0.0
    protein_g_per_100g: float = 0.0
    carbs_g_per_100g: float = 0.0
    fat_g_per_100g: float = 0.0
    room_shelf_life_days: int | None = None
    fridge_shelf_life_days: int | None = None
    freezer_shelf_life_days: int | None = None
    max_extra_quantity: float = 0.0
    extra_step_quantity: float | None = None

    @property
    def procurement_ready(self) -> bool:
        return self.purchase_mode != "regular" or (
            self.purchase_increment is not None
            and self.purchase_increment > 0
            and self.price_per_default_unit is not None
            and self.price_per_default_unit >= 0
        )

    @property
    def max_shelf_life_days(self) -> int:
        values = (
            self.room_shelf_life_days,
            self.fridge_shelf_life_days,
            self.freezer_shelf_life_days,
        )
        return max((value for value in values if value is not None), default=0)

    def nutrition_for(self, quantity: float) -> dict[str, float]:
        grams = quantity * self.grams_per_unit
        return {
            "calories": grams * self.calories_per_100g / 100.0,
            "protein_g": grams * self.protein_g_per_100g / 100.0,
            "fat_g": grams * self.fat_g_per_100g / 100.0,
            "carb_g": grams * self.carbs_g_per_100g / 100.0,
        }


@dataclass(frozen=True)
class DishCandidate:
    """Đơn vị quyết định nhỏ nhất của Planner V3."""

    dish_id: int
    name: str
    dish_type: DishType
    cooking_method: CookingMethod | None
    calories: float
    protein_g: float
    fat_g: float
    carb_g: float
    estimated_cost: float
    ingredient_ids: tuple[int, ...] = ()
    ingredients: tuple[DishIngredientSnapshot, ...] = ()
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class ComposedMeal:
    """Bữa được ghép động khi planner chạy; không có bảng dynamic_meals."""

    slot: MealType
    dishes: tuple[DishCandidate, ...]

    @property
    def calories(self) -> float:
        return sum(d.calories for d in self.dishes)

    @property
    def protein_g(self) -> float:
        return sum(d.protein_g for d in self.dishes)

    @property
    def fat_g(self) -> float:
        return sum(d.fat_g for d in self.dishes)

    @property
    def carb_g(self) -> float:
        return sum(d.carb_g for d in self.dishes)

    @property
    def estimated_cost(self) -> float:
        return sum(d.estimated_cost for d in self.dishes)

    @property
    def ingredient_ids(self) -> tuple[int, ...]:
        return tuple(i for dish in self.dishes for i in dish.ingredient_ids)


@dataclass(frozen=True)
class StructuredWarning:
    code: str
    message: str
    details: dict[str, float | int | str] = field(default_factory=dict)


@dataclass(frozen=True)
class InfeasibleReason:
    code: str
    message: str
    details: dict[str, float | int | str] = field(default_factory=dict)


@dataclass(frozen=True)
class PlanMetrics:
    average_calorie_deviation_pct: float = 0.0
    maximum_calorie_deviation_pct: float = 0.0
    protein_shortage_pct: float = 0.0
    repeat_counts: dict[str, int] = field(default_factory=dict)
    solver_time_ms: int = 0
    nutrition_score: int = 0
    purchase_cost: float = 0.0
    consumption_value: float = 0.0
    expired_waste_value: float = 0.0
    ending_carryover_value: float = 0.0
    shopping_days: int = 0


@dataclass(frozen=True)
class PlannerMetadata:
    algorithm_version: str = "dish-cpsat-v1"
    plan_signature: str = ""
    solver_status: str = "unknown"


@dataclass(frozen=True)
class QualityPolicy:
    calorie_deviation_weight: int = 10
    protein_shortage_weight: int = 16
    macro_deviation_weight: int = 3
    # Quality phase is lexicographic in spirit: after nutrition has reached a
    # small tolerance, avoiding repeated dishes must outweigh a modest price
    # difference.  Costs are measured in thousands of VND in that phase.
    savory_repeat_penalty: int = 80
    side_repeat_penalty: int = 60
    breakfast_repeat_penalty: int = 80
    staple_repeat_penalty: int = 40
    same_day_repeat_penalty: int = 500
    consecutive_repeat_penalty: int = 300
    preferred_tag_bonus: int = 5
    cooking_method_repeat_penalty: int = 20
    cost_weight: int = 1
    quality_nutrition_slack_pct: int = 5
    timeout_seconds: float = 0.30


@dataclass(frozen=True)
class MealPlanEntity:
    id: int | None
    user_id: int
    name: str = "Thực đơn tuần"
    start_date: date | None = None
    end_date: date | None = None
    budget_limit: float | None = None
    total_cost: float = 0
    total_calories: float = 0
    plan_data: dict = field(default_factory=dict)
    created_at: datetime | None = None


@dataclass(frozen=True)
class PlanRequest:
    """Yêu cầu đã chuẩn hóa từ profile + form generate."""

    user_id: int
    days: int
    meals_per_day: int
    budget_limit: float | None
    target_calories: float
    target_protein_g: float
    target_fat_g: float
    target_carb_g: float
    excluded_ingredient_ids: list[int] = field(default_factory=list)
    preferred_tags: list[str] = field(default_factory=list)
    previous_plan_signature: str | None = None
    inventory_lots: tuple["InventoryLotSnapshot", ...] = ()
    inventory_fingerprint: str | None = None
    ledger_enabled: bool = False


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
class ValidationResult:
    status: str
    hard_violations: list[str] = field(default_factory=list)
    warnings: list[StructuredWarning] = field(default_factory=list)
    infeasible_reasons: list[InfeasibleReason] = field(default_factory=list)

    @property
    def is_feasible(self) -> bool:
        return self.status != "infeasible"


@dataclass(frozen=True)
class PlannedMeal:
    """JSON-friendly representation of a dynamic composed meal."""

    name: str
    meal_type: str
    components: list[str]
    calories: float
    protein_g: float
    fat_g: float
    carb_g: float
    cost: float
    dishes: list[dict] = field(default_factory=list)
    candidate_type: str = "dynamic_meal"


@dataclass(frozen=True)
class PlannedDay:
    day: int
    date: str | None
    meals: list[PlannedMeal]
    day_calories: float
    day_cost: float

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.shared.enums import MealType


class SavedIngredientAdjustment(BaseModel):
    dish_id: int = Field(gt=0)
    ingredient_id: int = Field(gt=0)
    extra_quantity: float = Field(gt=0)


class SavedMealSlot(BaseModel):
    """Client chỉ gửi slot và lựa chọn dish; role luôn lấy từ database."""

    slot: MealType
    dish_ids: list[int] = Field(min_length=1, max_length=3)
    adjustments: list[SavedIngredientAdjustment] = Field(default_factory=list)

    @field_validator("dish_ids")
    @classmethod
    def unique_positive_dish_ids(cls, value: list[int]) -> list[int]:
        if any(dish_id <= 0 for dish_id in value) or len(value) != len(set(value)):
            raise ValueError("dish_ids phải dương và không trùng")
        return value
class SavedPlanDay(BaseModel):
    day: int = Field(ge=1, le=7)
    meals: list[SavedMealSlot] = Field(min_length=2, max_length=3)

    @model_validator(mode="after")
    def unique_slots(self) -> "SavedPlanDay":
        slots = [meal.slot for meal in self.meals]
        if len(slots) != len(set(slots)):
            raise ValueError("mỗi slot chỉ được xuất hiện một lần trong ngày")
        return self


class MealPlanCreate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    start_date: date
    budget_limit: float | None = Field(default=None, gt=0)
    source_fingerprint: str = Field(min_length=64, max_length=64)
    days: list[SavedPlanDay] = Field(min_length=1, max_length=7)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = " ".join(value.split())
        if not normalized:
            raise ValueError("tên thực đơn không được để trống")
        return normalized

    @model_validator(mode="after")
    def days_are_contiguous(self) -> "MealPlanCreate":
        days = [day.day for day in self.days]
        if len(days) != len(set(days)) or sorted(days) != list(range(1, len(days) + 1)):
            raise ValueError("day phải liên tục từ 1 và không trùng")
        return self


class MealPlanResponse(BaseModel):
    id: int
    user_id: int
    name: str
    start_date: date
    end_date: date | None
    budget_limit: float | None
    total_cost: float
    total_calories: float
    plan_data: dict
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class GenerateMealPlanRequest(BaseModel):
    days: int | None = Field(default=None, ge=1, le=7)
    meals_per_day: Literal[2, 3] | None = None
    budget_limit: float | None = Field(default=None, gt=0)
    preferred_tags: list[str] = Field(default_factory=list, max_length=12)
    seed: int | None = None
    previous_plan_signature: str | None = Field(default=None, max_length=4096)
    start_date: date | None = None

    @field_validator("preferred_tags")
    @classmethod
    def normalize_tags(cls, value: list[str]) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()
        for tag in value:
            normalized = " ".join(tag.split())
            if not normalized or len(normalized) > 64:
                continue
            key = normalized.casefold()
            if key not in seen:
                result.append(normalized)
                seen.add(key)
        return result


class GeneratedMealPlanResponse(BaseModel):
    user_id: int
    name: str
    start_date: date | None
    end_date: date | None
    budget_limit: float | None
    total_cost: float
    total_calories: float
    plan_data: dict


class InfeasibleReasonResponse(BaseModel):
    code: str
    message: str
    details: dict[str, float | int | str] = Field(default_factory=dict)


class InfeasiblePlanResponse(BaseModel):
    status: str = "infeasible"
    reasons: list[InfeasibleReasonResponse] = Field(default_factory=list)
    warnings: list[dict] = Field(default_factory=list)

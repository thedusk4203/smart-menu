from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.shared.enums import CookingMethod, DishType, FoodGroup, UserRole


class DashboardSummary(BaseModel):
    users_total: int
    users_active: int
    users_locked: int
    ingredients_total: int
    ingredients_active: int
    dishes_total: int
    planner_ready_dishes: int
    breakfast_count: int
    staple_count: int
    savory_count: int
    vegetable_count: int
    soup_count: int
    missing_price: int
    missing_nutrition: int
    missing_conversion: int
    incomplete_dishes: int
    duplicate_names: int
    open_quality_issues: int
    last_import_at: datetime | None = None


class AdminUserItem(BaseModel):
    id: int
    email: EmailStr
    full_name: str | None = None
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AdminUserPage(BaseModel):
    items: list[AdminUserItem]
    total: int
    limit: int
    offset: int


class AdminUserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)
    role: UserRole = UserRole.USER


class AdminUserRoleUpdate(BaseModel):
    role: UserRole


class AdminUserStatusUpdate(BaseModel):
    is_active: bool


class ActiveUpdate(BaseModel):
    is_active: bool


class NutritionPayload(BaseModel):
    calories: float = Field(default=0, ge=0)
    protein_g: float = Field(default=0, ge=0)
    carbs_g: float = Field(default=0, ge=0)
    fat_g: float = Field(default=0, ge=0)
    fiber_g: float = Field(default=0, ge=0)


class PricePayload(BaseModel):
    price: float = Field(ge=0)
    unit: str = Field(min_length=1, max_length=20)
    price_per_default_unit: float = Field(ge=0)
    source: str | None = Field(default=None, max_length=255)
    recorded_at: datetime | None = None


class AdminIngredientWrite(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    food_group: FoodGroup
    default_unit: str = Field(default="g", min_length=1, max_length=20)
    grams_per_unit: float = Field(default=1, gt=0)
    is_active: bool = True
    nutrition: NutritionPayload | None = None
    price: PricePayload | None = None

    @field_validator("name", "default_unit")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return " ".join(value.split())


class AdminIngredientItem(BaseModel):
    id: int
    name: str
    food_group: FoodGroup
    default_unit: str
    grams_per_unit: float
    is_active: bool
    calories: float | None = None
    protein_g: float | None = None
    carbs_g: float | None = None
    fat_g: float | None = None
    fiber_g: float | None = None
    latest_price: float | None = None
    price_unit: str | None = None
    latest_price_per_unit: float | None = None
    price_source: str | None = None
    price_recorded_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    missing_price: bool
    missing_nutrition: bool
    missing_conversion: bool


class AdminIngredientPage(BaseModel):
    items: list[AdminIngredientItem]
    total: int
    limit: int
    offset: int


class DishIngredientPayload(BaseModel):
    ingredient_id: int
    quantity: float = Field(gt=0)
    unit: str = Field(min_length=1, max_length=20)


class AdminDishWrite(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    dish_type: DishType
    cooking_method: CookingMethod | None = None
    description: str | None = None
    instructions: str | None = None
    tags: list[str] = []
    is_active: bool = True
    ingredients: list[DishIngredientPayload] = []

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        return " ".join(value.split())


class AdminDishIngredient(BaseModel):
    ingredient_id: int
    name: str
    quantity: float
    unit: str
    missing_price: bool
    missing_nutrition: bool


class AdminDishItem(BaseModel):
    id: int
    name: str
    dish_type: DishType
    cooking_method: CookingMethod | None = None
    description: str | None = None
    instructions: str | None = None
    tags: list[str] = []
    is_active: bool
    total_calories: float
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float
    estimated_cost: float
    ingredient_count: int
    missing_recipe: bool
    missing_price: bool
    missing_nutrition: bool
    created_at: datetime
    updated_at: datetime
    ingredients: list[AdminDishIngredient] = []


class AdminDishPage(BaseModel):
    items: list[AdminDishItem]
    total: int
    limit: int
    offset: int


class QualityIssue(BaseModel):
    entity_type: Literal["ingredient", "dish"]
    entity_id: int
    entity_name: str
    code: str
    severity: Literal["error", "warning"]
    title: str
    detail: str
    updated_at: datetime


class QualityIssuePage(BaseModel):
    items: list[QualityIssue]
    total: int
    limit: int
    offset: int


class ImportPreviewResponse(BaseModel):
    job_id: int
    entity_type: Literal["ingredients", "dishes"]
    filename: str
    total_rows: int
    valid_rows: int
    errors: list[dict]
    warnings: list[dict]
    conflicts: list[dict]
    preview: list[dict]
    can_commit: bool


class ImportCommitRequest(BaseModel):
    replace_rows: list[int] = Field(default_factory=list)


class ImportJobItem(BaseModel):
    id: int
    entity_type: str
    filename: str
    status: str
    total_rows: int
    valid_rows: int
    error_count: int
    created_by: int
    created_at: datetime
    completed_at: datetime | None = None


class ImportJobPage(BaseModel):
    items: list[ImportJobItem]
    total: int
    limit: int
    offset: int

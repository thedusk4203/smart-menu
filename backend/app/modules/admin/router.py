from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, File, Query, Response, UploadFile, status
from sqlmodel import Session

from app.core.database import get_session
from app.core.deps import require_data_editor, require_super_admin
from app.modules.admin.schemas import (
    ActiveUpdate,
    AdminDishItem,
    AdminDishPage,
    AdminDishWrite,
    AdminIngredientItem,
    AdminIngredientPage,
    AdminIngredientWrite,
    AdminMealSetItem,
    AdminMealSetPage,
    AdminMealSetWrite,
    AdminUserCreate,
    AdminUserItem,
    AdminUserPage,
    AdminUserRoleUpdate,
    AdminUserStatusUpdate,
    DashboardSummary,
    ImportCommitRequest,
    ImportJobPage,
    ImportPreviewResponse,
    QualityIssuePage,
)
from app.modules.admin.use_cases import AdminService
from app.modules.identity.domain import UserEntity
from app.shared.enums import DishType, FoodGroup, MealType, UserRole


router = APIRouter(prefix="/api/admin", tags=["admin"])


def get_admin_service(session: Session = Depends(get_session)) -> AdminService:
    return AdminService(session)


@router.get("/dashboard/summary", response_model=DashboardSummary)
def dashboard_summary(
    service: AdminService = Depends(get_admin_service),
    _: UserEntity = Depends(require_data_editor),
):
    return service.dashboard()


# --------------------------------------------------------------------------- users
@router.get("/users", response_model=AdminUserPage)
def list_users(
    search: str | None = None,
    role: UserRole | None = None,
    is_active: bool | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: AdminService = Depends(get_admin_service),
    _: UserEntity = Depends(require_super_admin),
):
    return service.list_users(search, role.value if role else None, is_active, limit, offset)


@router.post("/users", response_model=AdminUserItem, status_code=status.HTTP_201_CREATED)
def create_user(
    data: AdminUserCreate,
    service: AdminService = Depends(get_admin_service),
    current_user: UserEntity = Depends(require_super_admin),
):
    return service.create_user(data, current_user.id)


@router.patch("/users/{user_id}/role", response_model=AdminUserItem)
def update_user_role(
    user_id: int,
    data: AdminUserRoleUpdate,
    service: AdminService = Depends(get_admin_service),
    current_user: UserEntity = Depends(require_super_admin),
):
    return service.update_user_role(user_id, data.role, current_user.id)


@router.patch("/users/{user_id}/status", response_model=AdminUserItem)
def update_user_status(
    user_id: int,
    data: AdminUserStatusUpdate,
    service: AdminService = Depends(get_admin_service),
    current_user: UserEntity = Depends(require_super_admin),
):
    return service.update_user_status(user_id, data.is_active, current_user.id)


# --------------------------------------------------------------------- ingredients
@router.get("/ingredients", response_model=AdminIngredientPage)
def list_ingredients(
    search: str | None = None,
    food_group: FoodGroup | None = None,
    status_filter: Literal["active", "inactive"] | None = Query(default=None, alias="status"),
    quality: Literal["missing_price", "missing_nutrition", "missing_conversion"] | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: AdminService = Depends(get_admin_service),
    _: UserEntity = Depends(require_data_editor),
):
    return service.list_ingredients(
        search, food_group.value if food_group else None, status_filter, quality, limit, offset
    )


@router.get("/ingredients/{ingredient_id}", response_model=AdminIngredientItem)
def get_ingredient(
    ingredient_id: int,
    service: AdminService = Depends(get_admin_service),
    _: UserEntity = Depends(require_data_editor),
):
    return service._ingredient_from_db(ingredient_id)


@router.post("/ingredients", response_model=AdminIngredientItem, status_code=status.HTTP_201_CREATED)
def create_ingredient(
    data: AdminIngredientWrite,
    service: AdminService = Depends(get_admin_service),
    current_user: UserEntity = Depends(require_data_editor),
):
    return service.save_ingredient(data, current_user.id)


@router.put("/ingredients/{ingredient_id}", response_model=AdminIngredientItem)
def update_ingredient(
    ingredient_id: int,
    data: AdminIngredientWrite,
    service: AdminService = Depends(get_admin_service),
    current_user: UserEntity = Depends(require_data_editor),
):
    return service.save_ingredient(data, current_user.id, ingredient_id)


@router.patch("/ingredients/{ingredient_id}/active", response_model=AdminIngredientItem)
def set_ingredient_active(
    ingredient_id: int,
    data: ActiveUpdate,
    service: AdminService = Depends(get_admin_service),
    current_user: UserEntity = Depends(require_data_editor),
):
    return service.set_ingredient_active(ingredient_id, data.is_active, current_user.id)


# -------------------------------------------------------------------------- dishes
@router.get("/dishes", response_model=AdminDishPage)
def list_dishes(
    search: str | None = None,
    dish_type: DishType | None = None,
    status_filter: Literal["active", "inactive"] | None = Query(default=None, alias="status"),
    quality: Literal["missing_recipe", "missing_price", "missing_nutrition"] | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: AdminService = Depends(get_admin_service),
    _: UserEntity = Depends(require_data_editor),
):
    return service.list_dishes(search, dish_type.value if dish_type else None, status_filter, quality, limit, offset)


@router.get("/dishes/{dish_id}", response_model=AdminDishItem)
def get_dish(
    dish_id: int,
    service: AdminService = Depends(get_admin_service),
    _: UserEntity = Depends(require_data_editor),
):
    return service._dish_from_db(dish_id)


@router.post("/dishes", response_model=AdminDishItem, status_code=status.HTTP_201_CREATED)
def create_dish(
    data: AdminDishWrite,
    service: AdminService = Depends(get_admin_service),
    current_user: UserEntity = Depends(require_data_editor),
):
    return service.save_dish(data, current_user.id)


@router.put("/dishes/{dish_id}", response_model=AdminDishItem)
def update_dish(
    dish_id: int,
    data: AdminDishWrite,
    service: AdminService = Depends(get_admin_service),
    current_user: UserEntity = Depends(require_data_editor),
):
    return service.save_dish(data, current_user.id, dish_id)


@router.patch("/dishes/{dish_id}/active", response_model=AdminDishItem)
def set_dish_active(
    dish_id: int,
    data: ActiveUpdate,
    service: AdminService = Depends(get_admin_service),
    current_user: UserEntity = Depends(require_data_editor),
):
    return service.set_dish_active(dish_id, data.is_active, current_user.id)


# ----------------------------------------------------------------------- meal sets
@router.get("/meal-sets", response_model=AdminMealSetPage)
def list_meal_sets(
    search: str | None = None,
    meal_type: MealType | None = None,
    status_filter: Literal["active", "inactive"] | None = Query(default=None, alias="status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: AdminService = Depends(get_admin_service),
    _: UserEntity = Depends(require_data_editor),
):
    return service.list_meal_sets(search, meal_type.value if meal_type else None, status_filter, limit, offset)


@router.get("/meal-sets/{meal_set_id}", response_model=AdminMealSetItem)
def get_meal_set(
    meal_set_id: int,
    service: AdminService = Depends(get_admin_service),
    _: UserEntity = Depends(require_data_editor),
):
    return service._meal_set_from_db(meal_set_id)


@router.post("/meal-sets", response_model=AdminMealSetItem, status_code=status.HTTP_201_CREATED)
def create_meal_set(
    data: AdminMealSetWrite,
    service: AdminService = Depends(get_admin_service),
    current_user: UserEntity = Depends(require_data_editor),
):
    return service.save_meal_set(data, current_user.id)


@router.put("/meal-sets/{meal_set_id}", response_model=AdminMealSetItem)
def update_meal_set(
    meal_set_id: int,
    data: AdminMealSetWrite,
    service: AdminService = Depends(get_admin_service),
    current_user: UserEntity = Depends(require_data_editor),
):
    return service.save_meal_set(data, current_user.id, meal_set_id)


@router.patch("/meal-sets/{meal_set_id}/active", response_model=AdminMealSetItem)
def set_meal_set_active(
    meal_set_id: int,
    data: ActiveUpdate,
    service: AdminService = Depends(get_admin_service),
    current_user: UserEntity = Depends(require_data_editor),
):
    return service.set_meal_set_active(meal_set_id, data.is_active, current_user.id)


# ------------------------------------------------------------------------- quality
@router.get("/quality/issues", response_model=QualityIssuePage)
def list_quality_issues(
    entity_type: Literal["ingredient", "dish", "meal_set"] | None = None,
    severity: Literal["error", "warning"] | None = None,
    code: str | None = None,
    search: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: AdminService = Depends(get_admin_service),
    _: UserEntity = Depends(require_data_editor),
):
    return service.list_quality_issues(entity_type, severity, code, search, limit, offset)


# ------------------------------------------------------------------------- imports
@router.get("/imports/template")
def download_import_template(
    entity_type: Literal["ingredients", "dishes"],
    format: Literal["csv", "xlsx"] = "xlsx",
    service: AdminService = Depends(get_admin_service),
    _: UserEntity = Depends(require_data_editor),
):
    content, media_type, filename = service.import_template(entity_type, format)
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/imports/preview", response_model=ImportPreviewResponse)
async def preview_import(
    entity_type: Literal["ingredients", "dishes"],
    file: UploadFile = File(...),
    service: AdminService = Depends(get_admin_service),
    current_user: UserEntity = Depends(require_data_editor),
):
    content = await file.read()
    return service.preview_import(entity_type, file.filename or "import.csv", content, current_user.id)


@router.post("/imports/{job_id}/commit")
def commit_import(
    job_id: int,
    data: ImportCommitRequest,
    service: AdminService = Depends(get_admin_service),
    current_user: UserEntity = Depends(require_data_editor),
):
    return service.commit_import(job_id, data.replace_rows, current_user.id)


@router.get("/imports", response_model=ImportJobPage)
def list_import_jobs(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: AdminService = Depends(get_admin_service),
    _: UserEntity = Depends(require_data_editor),
):
    return service.list_import_jobs(limit, offset)

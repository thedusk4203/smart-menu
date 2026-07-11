from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError, jwt

from app.core.deps import get_current_user
from app.dependencies import (
    get_build_shopping_list_use_case, get_get_meal_plan_use_case,
    get_shopping_list_repository, get_shopping_share_repository,
)
from app.core.config import settings
from app.modules.identity.domain import UserEntity
from app.modules.meal_planning.use_cases import GetMealPlanUseCase
from app.modules.shopping_lists.schemas import (
    PublicShoppingListResponse, PurchaseUpdate, ShoppingListResponse, ShoppingShareResponse,
)
from app.modules.shopping_lists.use_cases import BuildShoppingListUseCase


router = APIRouter(prefix="/api/meal-plans", tags=["shopping-lists"])
public_router = APIRouter(prefix="/api/public/shopping-lists", tags=["public-shopping-lists"])


def _ensure_owner(plan, user: UserEntity) -> None:
    if plan.user_id != user.id and user.role.value not in {"admin", "super_admin"}:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Không có quyền với thực đơn này")


def _share_token(share: dict) -> str:
    return jwt.encode(
        {"scope": "shopping_list_share", "share_id": str(share["id"]), "exp": share["expires_at"]},
        settings.secret_key,
        algorithm=settings.algorithm,
    )


def _read_share_token(token: str) -> str:
    try:
        data = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        if data.get("scope") != "shopping_list_share" or not data.get("share_id"):
            raise JWTError("invalid scope")
        return str(data["share_id"])
    except JWTError as exc:
        raise HTTPException(status.HTTP_410_GONE, "Liên kết chia sẻ không hợp lệ hoặc đã hết hạn") from exc


@router.get("/{plan_id}/shopping-list", response_model=ShoppingListResponse)
def shopping_list(
    plan_id: int,
    current_user: UserEntity = Depends(get_current_user),
    plans: GetMealPlanUseCase = Depends(get_get_meal_plan_use_case),
    build: BuildShoppingListUseCase = Depends(get_build_shopping_list_use_case),
):
    plan = plans.execute(plan_id)
    _ensure_owner(plan, current_user)
    return build.execute(plan)


@router.patch("/{plan_id}/shopping-list/items/{item_id}", response_model=ShoppingListResponse)
def update_shopping_item(
    plan_id: int,
    item_id: int,
    data: PurchaseUpdate,
    current_user: UserEntity = Depends(get_current_user),
    plans: GetMealPlanUseCase = Depends(get_get_meal_plan_use_case),
    build: BuildShoppingListUseCase = Depends(get_build_shopping_list_use_case),
    lists=Depends(get_shopping_list_repository),
):
    plan = plans.execute(plan_id)
    _ensure_owner(plan, current_user)
    build.execute(plan)
    if lists.set_purchased(plan_id, item_id, data.is_purchased) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy nguyên liệu trong danh sách")
    return build.execute(plan)


@router.post("/{plan_id}/shopping-list/share", response_model=ShoppingShareResponse)
def share_shopping_list(
    plan_id: int,
    current_user: UserEntity = Depends(get_current_user),
    plans: GetMealPlanUseCase = Depends(get_get_meal_plan_use_case),
    build: BuildShoppingListUseCase = Depends(get_build_shopping_list_use_case),
    shares=Depends(get_shopping_share_repository),
):
    plan = plans.execute(plan_id)
    _ensure_owner(plan, current_user)
    build.execute(plan)
    share = shares.get_or_create(plan_id)
    return ShoppingShareResponse(token=_share_token(share), expires_at=share["expires_at"])


@router.delete("/{plan_id}/shopping-list/share", status_code=status.HTTP_204_NO_CONTENT)
def revoke_shopping_share(
    plan_id: int,
    current_user: UserEntity = Depends(get_current_user),
    plans: GetMealPlanUseCase = Depends(get_get_meal_plan_use_case),
    shares=Depends(get_shopping_share_repository),
):
    plan = plans.execute(plan_id)
    _ensure_owner(plan, current_user)
    shares.revoke(plan_id)


@public_router.get("/{token}", response_model=PublicShoppingListResponse)
def public_shopping_list(
    token: str,
    build: BuildShoppingListUseCase = Depends(get_build_shopping_list_use_case),
    plans: GetMealPlanUseCase = Depends(get_get_meal_plan_use_case),
    shares=Depends(get_shopping_share_repository),
):
    share = shares.get_active(_read_share_token(token))
    if share is None or share["expires_at"] <= datetime.now(timezone.utc):
        raise HTTPException(status.HTTP_410_GONE, "Liên kết chia sẻ đã hết hạn hoặc đã bị thu hồi")
    result = build.execute(plans.execute(share["meal_plan_id"]))
    return PublicShoppingListResponse(**result.model_dump(), expires_at=share["expires_at"])


@public_router.patch("/{token}/items/{item_id}", response_model=PublicShoppingListResponse)
def update_public_shopping_item(
    token: str,
    item_id: int,
    data: PurchaseUpdate,
    build: BuildShoppingListUseCase = Depends(get_build_shopping_list_use_case),
    plans: GetMealPlanUseCase = Depends(get_get_meal_plan_use_case),
    shares=Depends(get_shopping_share_repository),
    lists=Depends(get_shopping_list_repository),
):
    share = shares.get_active(_read_share_token(token))
    if share is None or share["expires_at"] <= datetime.now(timezone.utc):
        raise HTTPException(status.HTTP_410_GONE, "Liên kết chia sẻ đã hết hạn hoặc đã bị thu hồi")
    plan = plans.execute(share["meal_plan_id"])
    build.execute(plan)
    if lists.set_purchased(plan.id, item_id, data.is_purchased) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy nguyên liệu trong danh sách")
    result = build.execute(plan)
    return PublicShoppingListResponse(**result.model_dump(), expires_at=share["expires_at"])

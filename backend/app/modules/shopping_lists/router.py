from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from jose import JWTError, jwt

from app.core.deps import get_current_user
from app.dependencies import (
    get_active_shopping_share_use_case,
    get_build_shopping_list_use_case,
    get_get_meal_plan_use_case,
    get_or_create_shopping_share_use_case,
    get_revoke_shopping_share_use_case,
    get_update_shopping_item_use_case,
    get_update_shopping_items_use_case,
)
from app.core.config import settings
from app.modules.identity.domain import UserEntity
from app.modules.meal_planning.use_cases import GetMealPlanUseCase
from app.modules.shopping_lists.schemas import (
    BulkPurchaseUpdate, PublicShoppingListResponse, PurchaseUpdate,
    ShoppingListResponse, ShoppingShareResponse,
)
from app.modules.shopping_lists.use_cases import (
    BuildShoppingListUseCase,
    GetActiveShoppingShareUseCase,
    GetOrCreateShoppingShareUseCase,
    RevokeShoppingShareUseCase,
    UpdateShoppingItemUseCase,
    UpdateShoppingItemsUseCase,
)


router = APIRouter(prefix="/api/meal-plans", tags=["shopping-lists"])
public_router = APIRouter(prefix="/api/public/shopping-lists", tags=["public-shopping-lists"])


def _ensure_owner(plan, user: UserEntity) -> None:
    if plan.user_id != user.id and user.role.value not in {"admin", "super_admin"}:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Không có quyền với thực đơn này")


def _share_token(share: dict, day: int | None = None, list_scope: str = "all") -> str:
    payload = {"scope": "shopping_list_share", "share_id": str(share["id"]), "exp": share["expires_at"]}
    if day is not None:
        payload["day"] = day
    payload["list_scope"] = list_scope
    return jwt.encode(
        payload,
        settings.secret_key,
        algorithm=settings.algorithm,
    )


def _read_share_token(
    token: str, *, include_scope: bool = False
) -> tuple[str, int | None] | tuple[str, int | None, str]:
    try:
        data = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        if data.get("scope") != "shopping_list_share" or not data.get("share_id"):
            raise JWTError("invalid scope")
        day = data.get("day")
        if day is not None and (not isinstance(day, int) or not 1 <= day <= 7):
            raise JWTError("invalid day")
        list_scope = str(data.get("list_scope") or ("usage_day" if day is not None else "all"))
        if list_scope not in {"all", "purchase_day", "usage_day"}:
            raise JWTError("invalid list scope")
        result = (str(data["share_id"]), day, list_scope)
        return result if include_scope else result[:2]
    except JWTError as exc:
        raise HTTPException(status.HTTP_410_GONE, "Liên kết chia sẻ không hợp lệ hoặc đã hết hạn") from exc


@router.get("/{plan_id}/shopping-list", response_model=ShoppingListResponse)
def shopping_list(
    plan_id: int,
    day: int | None = Query(default=None, ge=1, le=7),
    scope: Literal["all", "purchase_day", "usage_day"] | None = Query(default=None),
    current_user: UserEntity = Depends(get_current_user),
    plans: GetMealPlanUseCase = Depends(get_get_meal_plan_use_case),
    build: BuildShoppingListUseCase = Depends(get_build_shopping_list_use_case),
):
    plan = plans.execute(plan_id)
    _ensure_owner(plan, current_user)
    resolved_scope = scope if isinstance(scope, str) else None
    return build.execute(plan, day, resolved_scope)


@router.patch("/{plan_id}/shopping-list/items/{item_id}", response_model=ShoppingListResponse)
def update_shopping_item(
    plan_id: int,
    item_id: int,
    data: PurchaseUpdate,
    day: int | None = Query(default=None, ge=1, le=7),
    scope: Literal["all", "purchase_day", "usage_day"] | None = Query(default=None),
    current_user: UserEntity = Depends(get_current_user),
    plans: GetMealPlanUseCase = Depends(get_get_meal_plan_use_case),
    build: BuildShoppingListUseCase = Depends(get_build_shopping_list_use_case),
    update_item: UpdateShoppingItemUseCase = Depends(get_update_shopping_item_use_case),
):
    plan = plans.execute(plan_id)
    _ensure_owner(plan, current_user)
    resolved_scope = scope if isinstance(scope, str) else None
    visible = build.execute(plan, day, resolved_scope)
    if item_id not in {item.id for item in visible.items if item.id is not None}:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy item trong phạm vi danh sách")
    if update_item.execute(plan_id, item_id, data.is_purchased) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy nguyên liệu trong danh sách")
    return build.execute(plan, day, resolved_scope)


@router.patch("/{plan_id}/shopping-list/items", response_model=ShoppingListResponse)
def update_shopping_items(
    plan_id: int,
    data: BulkPurchaseUpdate,
    day: int | None = Query(default=None, ge=1, le=7),
    scope: Literal["all", "purchase_day", "usage_day"] | None = Query(default=None),
    current_user: UserEntity = Depends(get_current_user),
    plans: GetMealPlanUseCase = Depends(get_get_meal_plan_use_case),
    build: BuildShoppingListUseCase = Depends(get_build_shopping_list_use_case),
    update_items: UpdateShoppingItemsUseCase = Depends(
        get_update_shopping_items_use_case
    ),
):
    plan = plans.execute(plan_id)
    _ensure_owner(plan, current_user)
    resolved_scope = scope if isinstance(scope, str) else None
    visible = build.execute(plan, day, resolved_scope)
    requested_ids = set(data.item_ids)
    visible_ids = {item.id for item in visible.items if item.id is not None}
    if not requested_ids.issubset(visible_ids):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy nguyên liệu trong phạm vi danh sách")
    if not update_items.execute(plan_id, data.item_ids, data.is_purchased):
        raise HTTPException(status.HTTP_409_CONFLICT, "Danh sách đã thay đổi. Hãy tải lại rồi thử lại")
    return build.execute(plan, day, resolved_scope)


@router.post("/{plan_id}/shopping-list/share", response_model=ShoppingShareResponse)
def share_shopping_list(
    plan_id: int,
    day: int | None = Query(default=None, ge=1, le=7),
    scope: Literal["all", "purchase_day", "usage_day"] | None = Query(default=None),
    current_user: UserEntity = Depends(get_current_user),
    plans: GetMealPlanUseCase = Depends(get_get_meal_plan_use_case),
    build: BuildShoppingListUseCase = Depends(get_build_shopping_list_use_case),
    create_share: GetOrCreateShoppingShareUseCase = Depends(
        get_or_create_shopping_share_use_case
    ),
):
    plan = plans.execute(plan_id)
    _ensure_owner(plan, current_user)
    explicit_scope = scope if isinstance(scope, str) else None
    resolved_scope = explicit_scope or ("usage_day" if day is not None else "all")
    build.execute(plan, day, resolved_scope)
    share = create_share.execute(plan_id)
    return ShoppingShareResponse(
        token=_share_token(share, day, resolved_scope),
        expires_at=share["expires_at"],
        day=day,
        scope=resolved_scope,
    )


@router.delete("/{plan_id}/shopping-list/share", status_code=status.HTTP_204_NO_CONTENT)
def revoke_shopping_share(
    plan_id: int,
    current_user: UserEntity = Depends(get_current_user),
    plans: GetMealPlanUseCase = Depends(get_get_meal_plan_use_case),
    revoke_share: RevokeShoppingShareUseCase = Depends(
        get_revoke_shopping_share_use_case
    ),
):
    plan = plans.execute(plan_id)
    _ensure_owner(plan, current_user)
    revoke_share.execute(plan_id)


@public_router.get("/{token}", response_model=PublicShoppingListResponse)
def public_shopping_list(
    token: str,
    build: BuildShoppingListUseCase = Depends(get_build_shopping_list_use_case),
    plans: GetMealPlanUseCase = Depends(get_get_meal_plan_use_case),
    get_share: GetActiveShoppingShareUseCase = Depends(get_active_shopping_share_use_case),
):
    share_id, day, scope = _read_share_token(token, include_scope=True)
    share = get_share.execute(share_id)
    if share is None or share["expires_at"] <= datetime.now(timezone.utc):
        raise HTTPException(status.HTTP_410_GONE, "Liên kết chia sẻ đã hết hạn hoặc đã bị thu hồi")
    result = build.execute(plans.execute(share["meal_plan_id"]), day, scope)
    return PublicShoppingListResponse(**result.model_dump(), expires_at=share["expires_at"])


@public_router.patch("/{token}/items/{item_id}", response_model=PublicShoppingListResponse)
def update_public_shopping_item(
    token: str,
    item_id: int,
    data: PurchaseUpdate,
    build: BuildShoppingListUseCase = Depends(get_build_shopping_list_use_case),
    plans: GetMealPlanUseCase = Depends(get_get_meal_plan_use_case),
    get_share: GetActiveShoppingShareUseCase = Depends(get_active_shopping_share_use_case),
    update_item: UpdateShoppingItemUseCase = Depends(get_update_shopping_item_use_case),
):
    share_id, day, scope = _read_share_token(token, include_scope=True)
    share = get_share.execute(share_id)
    if share is None or share["expires_at"] <= datetime.now(timezone.utc):
        raise HTTPException(status.HTTP_410_GONE, "Liên kết chia sẻ đã hết hạn hoặc đã bị thu hồi")
    plan = plans.execute(share["meal_plan_id"])
    visible = build.execute(plan, day, scope)
    if item_id not in {item.id for item in visible.items if item.id is not None}:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy item trong phạm vi liên kết")
    if update_item.execute(plan.id, item_id, data.is_purchased) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy nguyên liệu trong danh sách")
    result = build.execute(plan, day, scope)
    return PublicShoppingListResponse(**result.model_dump(), expires_at=share["expires_at"])


@public_router.patch("/{token}/items", response_model=PublicShoppingListResponse)
def update_public_shopping_items(
    token: str,
    data: BulkPurchaseUpdate,
    build: BuildShoppingListUseCase = Depends(get_build_shopping_list_use_case),
    plans: GetMealPlanUseCase = Depends(get_get_meal_plan_use_case),
    get_share: GetActiveShoppingShareUseCase = Depends(get_active_shopping_share_use_case),
    update_items: UpdateShoppingItemsUseCase = Depends(
        get_update_shopping_items_use_case
    ),
):
    share_id, day, scope = _read_share_token(token, include_scope=True)
    share = get_share.execute(share_id)
    if share is None or share["expires_at"] <= datetime.now(timezone.utc):
        raise HTTPException(status.HTTP_410_GONE, "Liên kết chia sẻ đã hết hạn hoặc đã bị thu hồi")
    plan = plans.execute(share["meal_plan_id"])
    visible = build.execute(plan, day, scope)
    requested_ids = set(data.item_ids)
    visible_ids = {item.id for item in visible.items if item.id is not None}
    if not requested_ids.issubset(visible_ids):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy nguyên liệu trong phạm vi liên kết")
    if not update_items.execute(plan.id, data.item_ids, data.is_purchased):
        raise HTTPException(status.HTTP_409_CONFLICT, "Danh sách đã thay đổi. Hãy tải lại rồi thử lại")
    result = build.execute(plan, day, scope)
    return PublicShoppingListResponse(**result.model_dump(), expires_at=share["expires_at"])

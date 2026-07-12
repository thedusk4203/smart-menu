from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

from app.core.database import get_session
from app.core.deps import get_current_user, require_super_admin
from app.dependencies import (
    get_create_empty_profile_use_case,
    get_create_user_use_case,
    get_delete_user_use_case,
    get_get_user_use_case,
    get_list_users_use_case,
    get_login_use_case,
    get_update_user_use_case,
)
from app.modules.identity.domain import UserEntity
from app.modules.identity.schemas import (
    RegisterRequest,
    TokenResponse,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from app.shared.enums import UserRole
from app.modules.identity.use_cases import (
    CreateUserUseCase,
    DeleteUserUseCase,
    GetUserUseCase,
    ListUsersUseCase,
    LoginUseCase,
    UpdateUserUseCase,
)
from app.modules.profiles.use_cases import CreateEmptyProfileUseCase

# ── Auth (/api/auth/*) ─────────────────────────────────────────────────────
auth_router = APIRouter(prefix="/api/auth", tags=["auth"])


@auth_router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    data: RegisterRequest,
    use_case: CreateUserUseCase = Depends(get_create_user_use_case),
    profile_use_case: CreateEmptyProfileUseCase = Depends(get_create_empty_profile_use_case),
):
    user = use_case.execute(data.email, data.password, UserRole.USER)
    profile_use_case.execute(user.id, data.full_name)
    return user.__dict__


@auth_router.post("/login", response_model=TokenResponse)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    use_case: LoginUseCase = Depends(get_login_use_case),
):
    token = use_case.execute(form.username, form.password)
    return TokenResponse(access_token=token)


@auth_router.post("/logout", status_code=status.HTTP_200_OK)
def logout(current_user: UserEntity = Depends(get_current_user)):
    return {"detail": f"Tạm biệt {current_user.email}. Vui lòng xoá token phía client."}


@auth_router.get("/me", response_model=UserResponse)
def me(current_user: UserEntity = Depends(get_current_user)):
    return current_user.__dict__


# ── Users admin (/api/users/*) ─────────────────────────────────────────────
router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("", response_model=list[UserResponse])
def list_users(
    limit: int = Query(100, le=500),
    offset: int = 0,
    use_case: ListUsersUseCase = Depends(get_list_users_use_case),
    _: UserEntity = Depends(require_super_admin),
):
    return [u.__dict__ for u in use_case.execute(limit, offset)]


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    use_case: GetUserUseCase = Depends(get_get_user_use_case),
    current_user: UserEntity = Depends(get_current_user),
):
    if current_user.role.value != "admin" and current_user.id != user_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Chỉ được xem tài khoản của chính mình")
    return use_case.execute(user_id).__dict__


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    data: UserCreate,
    use_case: CreateUserUseCase = Depends(get_create_user_use_case),
    profile_use_case: CreateEmptyProfileUseCase = Depends(get_create_empty_profile_use_case),
    _: UserEntity = Depends(require_super_admin),
):
    user = use_case.execute(data.email, data.password, data.role)
    profile_use_case.execute(user.id, data.full_name)
    return user.__dict__


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    data: UserUpdate,
    use_case: UpdateUserUseCase = Depends(get_update_user_use_case),
    _: UserEntity = Depends(require_super_admin),
):
    return use_case.execute(user_id, **data.model_dump(exclude_unset=True)).__dict__


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    use_case: DeleteUserUseCase = Depends(get_delete_user_use_case),
    _: UserEntity = Depends(require_super_admin),
):
    use_case.execute(user_id)

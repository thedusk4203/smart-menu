# File: backend/app/modules/identity/router.py
# Presentation layer: HTTP endpoints for account management (/api/users).
# Basic CRUD only — login/register (JWT) will be added when the team starts
# the authentication feature.
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status

from app.dependencies import (
    get_create_user_use_case,
    get_delete_user_use_case,
    get_get_user_use_case,
    get_list_users_use_case,
    get_update_user_use_case,
)
from app.modules.identity.schemas import UserCreate, UserResponse, UserUpdate
from app.modules.identity.use_cases import (
    CreateUserUseCase,
    DeleteUserUseCase,
    GetUserUseCase,
    ListUsersUseCase,
    UpdateUserUseCase,
)
from app.modules.profiles.use_cases import CreateEmptyProfileUseCase
from app.dependencies import get_create_empty_profile_use_case

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("", response_model=list[UserResponse])
def list_users(
    limit: int = Query(100, le=500),
    offset: int = 0,
    use_case: ListUsersUseCase = Depends(get_list_users_use_case),
):
    return [u.__dict__ for u in use_case.execute(limit, offset)]


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, use_case: GetUserUseCase = Depends(get_get_user_use_case)):
    return use_case.execute(user_id).__dict__


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    data: UserCreate,
    use_case: CreateUserUseCase = Depends(get_create_user_use_case),
    profile_use_case: CreateEmptyProfileUseCase = Depends(get_create_empty_profile_use_case),
):
    user = use_case.execute(data.email, data.password, data.role)
    profile_use_case.execute(user.id, data.full_name)
    return user.__dict__


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int, data: UserUpdate,
    use_case: UpdateUserUseCase = Depends(get_update_user_use_case),
):
    changes = data.model_dump(exclude_unset=True)
    return use_case.execute(user_id, **changes).__dict__


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, use_case: DeleteUserUseCase = Depends(get_delete_user_use_case)):
    use_case.execute(user_id)

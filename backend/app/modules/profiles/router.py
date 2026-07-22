from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from app.core.database import get_ai_state_session
from app.core.deps import get_current_user, require_admin
from app.dependencies import (
    get_add_exclusion_use_case,
    get_get_profile_use_case,
    get_list_exclusions_use_case,
    get_remove_exclusion_use_case,
    get_update_profile_use_case,
)
from app.modules.identity.domain import UserEntity
from app.modules.profiles.schemas import (
    AIPreferencesResponse, AIPreferencesUpdate, ExclusionCreate, ExclusionResponse,
    ProfileResponse, ProfileUpdate,
)
from app.modules.ai.personalization import (
    AIPreferenceStore, AuthenticatedAIRequestScope,
)
from app.modules.profiles.use_cases import (
    AddExclusionUseCase, GetProfileUseCase, ListExclusionsUseCase,
    RemoveExclusionUseCase, UpdateProfileUseCase,
)

router = APIRouter(prefix="/api/profiles", tags=["profiles"])


# ── /me (user tự quản lý hồ sơ của mình) ─────────────────────────────────

@router.get("/me", response_model=ProfileResponse)
def get_my_profile(
    current_user: UserEntity = Depends(get_current_user),
    use_case: GetProfileUseCase = Depends(get_get_profile_use_case),
):
    return use_case.execute(current_user.id).__dict__


@router.put("/me", response_model=ProfileResponse)
def update_my_profile(
    data: ProfileUpdate,
    current_user: UserEntity = Depends(get_current_user),
    use_case: UpdateProfileUseCase = Depends(get_update_profile_use_case),
):
    return use_case.execute(current_user.id, **data.model_dump(exclude_unset=True)).__dict__


@router.get("/me/ai-preferences", response_model=AIPreferencesResponse)
def get_my_ai_preferences(
    current_user: UserEntity = Depends(get_current_user),
    session: Session = Depends(get_ai_state_session),
):
    return AIPreferenceStore(session).get(
        AuthenticatedAIRequestScope(current_user.id)
    )


@router.put("/me/ai-preferences", response_model=AIPreferencesResponse)
def update_my_ai_preferences(
    data: AIPreferencesUpdate,
    current_user: UserEntity = Depends(get_current_user),
    session: Session = Depends(get_ai_state_session),
):
    return AIPreferenceStore(session).update(
        AuthenticatedAIRequestScope(current_user.id),
        personalization_enabled=data.personalization_enabled,
        notice_version=data.notice_version,
    )


@router.get("/me/exclusions", response_model=list[ExclusionResponse])
def get_my_exclusions(
    current_user: UserEntity = Depends(get_current_user),
    use_case: ListExclusionsUseCase = Depends(get_list_exclusions_use_case),
):
    return [e.__dict__ for e in use_case.execute(current_user.id)]


@router.post("/me/exclusions", response_model=ExclusionResponse, status_code=status.HTTP_201_CREATED)
def add_my_exclusion(
    data: ExclusionCreate,
    current_user: UserEntity = Depends(get_current_user),
    use_case: AddExclusionUseCase = Depends(get_add_exclusion_use_case),
):
    return use_case.execute(current_user.id, data.ingredient_id, data.reason.value).__dict__


@router.delete("/me/exclusions/{ingredient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_exclusion(
    ingredient_id: int,
    current_user: UserEntity = Depends(get_current_user),
    use_case: RemoveExclusionUseCase = Depends(get_remove_exclusion_use_case),
):
    use_case.execute(current_user.id, ingredient_id)


# ── /{user_id} (admin quản lý hồ sơ mọi người) ────────────────────────────

@router.get("/{user_id}", response_model=ProfileResponse)
def get_profile(
    user_id: int,
    use_case: GetProfileUseCase = Depends(get_get_profile_use_case),
    _: UserEntity = Depends(require_admin),
):
    return use_case.execute(user_id).__dict__


@router.put("/{user_id}", response_model=ProfileResponse)
def update_profile(
    user_id: int,
    data: ProfileUpdate,
    use_case: UpdateProfileUseCase = Depends(get_update_profile_use_case),
    _: UserEntity = Depends(require_admin),
):
    return use_case.execute(user_id, **data.model_dump(exclude_unset=True)).__dict__


@router.get("/{user_id}/exclusions", response_model=list[ExclusionResponse])
def list_exclusions(
    user_id: int,
    use_case: ListExclusionsUseCase = Depends(get_list_exclusions_use_case),
    _: UserEntity = Depends(require_admin),
):
    return [e.__dict__ for e in use_case.execute(user_id)]


@router.post("/{user_id}/exclusions", response_model=ExclusionResponse, status_code=status.HTTP_201_CREATED)
def add_exclusion(
    user_id: int,
    data: ExclusionCreate,
    use_case: AddExclusionUseCase = Depends(get_add_exclusion_use_case),
    _: UserEntity = Depends(require_admin),
):
    return use_case.execute(user_id, data.ingredient_id, data.reason.value).__dict__


@router.delete("/{user_id}/exclusions/{ingredient_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_exclusion(
    user_id: int,
    ingredient_id: int,
    use_case: RemoveExclusionUseCase = Depends(get_remove_exclusion_use_case),
    _: UserEntity = Depends(require_admin),
):
    use_case.execute(user_id, ingredient_id)

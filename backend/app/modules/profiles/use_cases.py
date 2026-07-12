from __future__ import annotations

from app.modules.profiles.domain import ExcludedIngredientEntity, UserProfileEntity
from app.modules.profiles.exceptions import (
    ExclusionAlreadyExistsError,
    ExclusionNotFoundError,
    ProfileNotFoundError,
)
from app.modules.profiles.ports import ExclusionRepositoryPort, UserProfileRepositoryPort


class CreateEmptyProfileUseCase:
    """Gọi bởi identity module ngay sau khi tạo tài khoản mới."""
    def __init__(self, repo: UserProfileRepositoryPort) -> None:
        self._repo = repo

    def execute(self, user_id: int, full_name: str | None = None) -> UserProfileEntity:
        return self._repo.create_empty(user_id, full_name)


class GetProfileUseCase:
    def __init__(self, repo: UserProfileRepositoryPort) -> None:
        self._repo = repo

    def execute(self, user_id: int) -> UserProfileEntity:
        profile = self._repo.get_by_user(user_id)
        if profile is None:
            raise ProfileNotFoundError(user_id)
        return profile


class UpdateProfileUseCase:
    def __init__(self, repo: UserProfileRepositoryPort) -> None:
        self._repo = repo

    def execute(self, user_id: int, **changes) -> UserProfileEntity:
        profile = self._repo.get_by_user(user_id)
        if profile is None:
            raise ProfileNotFoundError(user_id)
        updated = UserProfileEntity(**{**profile.__dict__, **changes})
        return self._repo.save(updated)


class ListExclusionsUseCase:
    def __init__(self, repo: ExclusionRepositoryPort) -> None:
        self._repo = repo

    def execute(self, user_id: int) -> list[ExcludedIngredientEntity]:
        return self._repo.list_by_user(user_id)


class AddExclusionUseCase:
    def __init__(self, repo: ExclusionRepositoryPort) -> None:
        self._repo = repo

    def execute(self, user_id: int, ingredient_id: int, reason: str) -> ExcludedIngredientEntity:
        if self._repo.get(user_id, ingredient_id) is not None:
            raise ExclusionAlreadyExistsError(ingredient_id)
        item = ExcludedIngredientEntity(id=None, user_id=user_id, ingredient_id=ingredient_id, reason=reason)
        return self._repo.add(item)


class RemoveExclusionUseCase:
    def __init__(self, repo: ExclusionRepositoryPort) -> None:
        self._repo = repo

    def execute(self, user_id: int, ingredient_id: int) -> None:
        if self._repo.get(user_id, ingredient_id) is None:
            raise ExclusionNotFoundError(ingredient_id)
        self._repo.remove(user_id, ingredient_id)

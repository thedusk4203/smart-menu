from __future__ import annotations

from app.modules.profiles.domain import ExcludedIngredientEntity, UserProfileEntity
from app.modules.profiles.exceptions import (
    ExclusionAlreadyExistsError,
    ExclusionNotFoundError,
    ProfileNotFoundError,
)
from app.modules.profiles.ports import ExclusionRepositoryPort, UserProfileRepositoryPort
from app.modules.nutrition.calculator import NutritionCalculator


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
        # Calorie target is derived data. Never trust a client-provided value,
        # and clear a stale target when the profile becomes incomplete.
        changes.pop("daily_calorie_target", None)
        values = {**profile.__dict__, **changes}
        required = (
            values["gender"],
            values["age"],
            values["height_cm"],
            values["weight_kg"],
        )
        if all(value is not None for value in required):
            target = NutritionCalculator.calculate_nutrition_target(
                gender=values["gender"],
                age=values["age"],
                height_cm=values["height_cm"],
                weight_kg=values["weight_kg"],
                activity_level=values["activity_level"],
                fitness_goal=values["goal"],
            )
            values["daily_calorie_target"] = float(target.target_calories)
        else:
            values["daily_calorie_target"] = None
        updated = UserProfileEntity(**values)
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

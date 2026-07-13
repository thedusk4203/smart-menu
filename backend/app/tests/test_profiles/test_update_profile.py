from __future__ import annotations

from app.modules.nutrition.calculator import NutritionCalculator
from app.modules.profiles.domain import UserProfileEntity
from app.modules.profiles.use_cases import UpdateProfileUseCase
from app.shared.enums import ActivityLevel, FitnessGoal, Gender


class ProfileRepository:
    def __init__(self, profile: UserProfileEntity) -> None:
        self.profile = profile

    def get_by_user(self, user_id: int) -> UserProfileEntity | None:
        return self.profile if self.profile.user_id == user_id else None

    def save(self, profile: UserProfileEntity) -> UserProfileEntity:
        self.profile = profile
        return profile


def test_complete_profile_update_calculates_and_persists_daily_calorie_target():
    repo = ProfileRepository(UserProfileEntity(user_id=7))

    updated = UpdateProfileUseCase(repo).execute(
        7,
        gender=Gender.MALE,
        age=30,
        height_cm=175,
        weight_kg=70,
        activity_level=ActivityLevel.MODERATE,
        goal=FitnessGoal.MAINTAIN,
        daily_calorie_target=1,
    )

    expected = NutritionCalculator.calculate_nutrition_target(
        gender=Gender.MALE,
        age=30,
        height_cm=175,
        weight_kg=70,
        activity_level=ActivityLevel.MODERATE,
        fitness_goal=FitnessGoal.MAINTAIN,
    )
    assert updated.daily_calorie_target == expected.target_calories
    assert updated.daily_calorie_target != 1


def test_incomplete_profile_update_clears_stale_daily_calorie_target():
    repo = ProfileRepository(
        UserProfileEntity(
            user_id=7,
            gender=Gender.MALE,
            age=30,
            height_cm=175,
            weight_kg=70,
            daily_calorie_target=2500,
        )
    )

    updated = UpdateProfileUseCase(repo).execute(7, weight_kg=None)

    assert updated.daily_calorie_target is None

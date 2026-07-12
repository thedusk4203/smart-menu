from __future__ import annotations

from sqlmodel import Session, select

from app.modules.profiles.domain import ExcludedIngredientEntity, UserProfileEntity
from app.modules.profiles.models import UserExcludedIngredientModel, UserProfileModel
from app.modules.profiles.ports import ExclusionRepositoryPort, UserProfileRepositoryPort
from app.shared.enums import ActivityLevel, FitnessGoal


def _to_entity(row: UserProfileModel) -> UserProfileEntity:
    return UserProfileEntity(
        user_id=row.user_id, full_name=row.full_name, gender=row.gender, age=row.age,
        height_cm=row.height_cm, weight_kg=row.weight_kg, activity_level=row.activity_level,
        goal=row.goal, meals_per_day=row.meals_per_day,
        daily_calorie_target=row.daily_calorie_target, daily_budget=row.daily_budget,
    )


class SqlUserProfileRepository(UserProfileRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_user(self, user_id: int) -> UserProfileEntity | None:
        row = self._session.exec(
            select(UserProfileModel).where(UserProfileModel.user_id == user_id)
        ).first()
        return _to_entity(row) if row else None

    def create_empty(self, user_id: int, full_name: str | None) -> UserProfileEntity:
        row = UserProfileModel(
            user_id=user_id, full_name=full_name,
            activity_level=ActivityLevel.SEDENTARY, goal=FitnessGoal.MAINTAIN, meals_per_day=3,
        )
        self._session.add(row)
        self._session.commit()
        self._session.refresh(row)
        return _to_entity(row)

    def save(self, profile: UserProfileEntity) -> UserProfileEntity:
        row = self._session.exec(
            select(UserProfileModel).where(UserProfileModel.user_id == profile.user_id)
        ).first()
        for f in ("full_name", "gender", "age", "height_cm", "weight_kg", "activity_level",
                  "goal", "meals_per_day", "daily_calorie_target", "daily_budget"):
            setattr(row, f, getattr(profile, f))
        self._session.add(row)
        self._session.commit()
        self._session.refresh(row)
        return _to_entity(row)


def _excl_to_entity(row: UserExcludedIngredientModel) -> ExcludedIngredientEntity:
    return ExcludedIngredientEntity(
        id=row.id, user_id=row.user_id, ingredient_id=row.ingredient_id, reason=row.reason.value
    )


class SqlExclusionRepository(ExclusionRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_by_user(self, user_id: int) -> list[ExcludedIngredientEntity]:
        rows = self._session.exec(
            select(UserExcludedIngredientModel).where(UserExcludedIngredientModel.user_id == user_id)
        ).all()
        return [_excl_to_entity(r) for r in rows]

    def get(self, user_id: int, ingredient_id: int) -> ExcludedIngredientEntity | None:
        row = self._session.exec(
            select(UserExcludedIngredientModel)
            .where(UserExcludedIngredientModel.user_id == user_id)
            .where(UserExcludedIngredientModel.ingredient_id == ingredient_id)
        ).first()
        return _excl_to_entity(row) if row else None

    def add(self, item: ExcludedIngredientEntity) -> ExcludedIngredientEntity:
        row = UserExcludedIngredientModel(
            user_id=item.user_id, ingredient_id=item.ingredient_id, reason=item.reason
        )
        self._session.add(row)
        self._session.commit()
        self._session.refresh(row)
        return _excl_to_entity(row)

    def remove(self, user_id: int, ingredient_id: int) -> None:
        row = self._session.exec(
            select(UserExcludedIngredientModel)
            .where(UserExcludedIngredientModel.user_id == user_id)
            .where(UserExcludedIngredientModel.ingredient_id == ingredient_id)
        ).first()
        if row:
            self._session.delete(row)
            self._session.commit()

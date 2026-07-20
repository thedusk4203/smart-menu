from __future__ import annotations

from sqlmodel import Session, select

from app.modules.meal_planning.domain import MealPlanEntity
from app.modules.meal_planning.models import MealPlanModel
from app.modules.meal_planning.ports import MealPlanRepositoryPort


def _to_entity(row: MealPlanModel) -> MealPlanEntity:
    return MealPlanEntity(
        id=row.id, user_id=row.user_id, name=row.name, start_date=row.start_date,
        end_date=row.end_date, budget_limit=row.budget_limit, total_cost=row.total_cost,
        total_calories=row.total_calories, plan_data=row.plan_data, created_at=row.created_at,
    )


class SqlMealPlanRepository(MealPlanRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, plan: MealPlanEntity) -> MealPlanEntity:
        row = MealPlanModel(
            user_id=plan.user_id, name=plan.name, start_date=plan.start_date, end_date=plan.end_date,
            budget_limit=plan.budget_limit, total_cost=plan.total_cost,
            total_calories=plan.total_calories, plan_data=plan.plan_data,
        )
        self._session.add(row)
        self._session.flush()
        self._session.refresh(row)
        return _to_entity(row)

    def list_by_user(self, user_id: int) -> list[MealPlanEntity]:
        rows = self._session.exec(
            select(MealPlanModel).where(MealPlanModel.user_id == user_id).order_by(MealPlanModel.created_at.desc())
        ).all()
        return [_to_entity(r) for r in rows]

    def get(self, plan_id: int) -> MealPlanEntity | None:
        row = self._session.get(MealPlanModel, plan_id)
        return _to_entity(row) if row else None

    def delete(self, plan_id: int) -> None:
        row = self._session.get(MealPlanModel, plan_id)
        if row:
            self._session.delete(row)
            self._session.flush()

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()

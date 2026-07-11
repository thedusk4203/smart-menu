# File: backend/app/modules/meals/repository.py
from __future__ import annotations

from sqlalchemy import text

from app.modules.meals.domain import MealEntity, MealFullEntity, MealIngredientEntity
from app.modules.meals.models import MealIngredientModel, MealModel
from app.modules.meals.ports import MealRepositoryPort


def _f(v):
    return float(v) if v is not None else 0.0


def _summary(row) -> MealFullEntity:
    return MealFullEntity(
        id=row.id, name=row.name, meal_type=row.meal_type, cooking_method=row.cooking_method,
        servings=row.servings, tags=row.tags, components=row.components or [], is_active=row.is_active,
        total_calories=_f(row.total_calories), total_protein_g=_f(row.total_protein_g),
        total_carbs_g=_f(row.total_carbs_g), total_fat_g=_f(row.total_fat_g),
        estimated_cost=_f(row.estimated_cost),
    )


def _to_entity(row: MealModel) -> MealEntity:
    return MealEntity(
        id=row.id, name=row.name, meal_type=row.meal_type, cooking_method=row.cooking_method,
        description=row.description, instructions=row.instructions, servings=row.servings,
        tags=row.tags, components=row.components or [], is_active=row.is_active,
    )


class SqlMealRepository(MealRepositoryPort):
    """Đọc tổng hợp qua view v_meals_full (tự tính dinh dưỡng + chi phí từ
    nguyên liệu); ghi qua ORM (MealModel, MealIngredientModel)."""

    def __init__(self, session) -> None:
        self._session = session

    def list_summary(self, meal_type, search, active_only, limit, offset) -> list[MealFullEntity]:
        sql = "SELECT * FROM v_meals_full WHERE 1=1"
        params: dict = {}
        if active_only:
            sql += " AND is_active = TRUE"
        if meal_type:
            sql += " AND meal_type = :mt"
            params["mt"] = meal_type
        if search:
            sql += " AND name ILIKE :kw"
            params["kw"] = f"%{search}%"
        sql += " ORDER BY name LIMIT :limit OFFSET :offset"
        params["limit"] = limit
        params["offset"] = offset
        rows = self._session.execute(text(sql), params).fetchall()
        return [_summary(r) for r in rows]

    def get_detail(self, meal_id: int) -> MealFullEntity | None:
        row = self._session.execute(text("SELECT * FROM v_meals_full WHERE id = :id"), {"id": meal_id}).first()
        if row is None:
            return None
        full = _summary(row)
        meal_row = self._session.get(MealModel, meal_id)
        ing_rows = self._session.execute(
            text("""SELECT mi.ingredient_id, i.name, mi.quantity, mi.unit
                     FROM meal_ingredients mi JOIN ingredients i ON i.id = mi.ingredient_id
                     WHERE mi.meal_id = :id ORDER BY i.name"""),
            {"id": meal_id},
        ).fetchall()
        ingredients = [
            MealIngredientEntity(ingredient_id=r.ingredient_id, name=r.name, quantity=_f(r.quantity), unit=r.unit)
            for r in ing_rows
        ]
        return MealFullEntity(**{**full.__dict__, "description": meal_row.description,
                                  "instructions": meal_row.instructions, "ingredients": ingredients})

    def get(self, meal_id: int) -> MealEntity | None:
        row = self._session.get(MealModel, meal_id)
        return _to_entity(row) if row else None

    def create(self, meal: MealEntity, ingredients: list[MealIngredientEntity]) -> MealEntity:
        row = MealModel(name=meal.name, meal_type=meal.meal_type, cooking_method=meal.cooking_method,
                         description=meal.description, instructions=meal.instructions,
                         servings=meal.servings, tags=meal.tags, components=meal.components)
        self._session.add(row)
        self._session.commit()
        self._session.refresh(row)
        for ing in ingredients:
            self._session.add(MealIngredientModel(meal_id=row.id, ingredient_id=ing.ingredient_id,
                                                    quantity=ing.quantity, unit=ing.unit))
        self._session.commit()
        return _to_entity(row)

    def save(self, meal: MealEntity) -> MealEntity:
        row = self._session.get(MealModel, meal.id)
        for f in ("name", "meal_type", "cooking_method", "description", "instructions",
                  "servings", "tags", "components", "is_active"):
            setattr(row, f, getattr(meal, f))
        self._session.add(row)
        self._session.commit()
        self._session.refresh(row)
        return _to_entity(row)

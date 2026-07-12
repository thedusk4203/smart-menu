from __future__ import annotations

from sqlalchemy import text
from sqlmodel import Session, select

from app.modules.ingredients.domain import IngredientEntity, IngredientFullEntity, NutritionFactsEntity
from app.modules.ingredients.models import IngredientModel, NutritionFactsModel
from app.modules.ingredients.ports import IngredientRepositoryPort


def _f(v):
    return float(v) if v is not None else None


def _to_entity(row: IngredientModel) -> IngredientEntity:
    return IngredientEntity(
        id=row.id, name=row.name, food_group=row.food_group,
        default_unit=row.default_unit, grams_per_unit=row.grams_per_unit, is_active=row.is_active,
    )


def _full_from_row(row) -> IngredientFullEntity:
    return IngredientFullEntity(
        id=row.id, name=row.name, food_group=row.food_group, default_unit=row.default_unit,
        grams_per_unit=_f(row.grams_per_unit), is_active=row.is_active,
        calories=_f(row.calories), protein_g=_f(row.protein_g), carbs_g=_f(row.carbs_g),
        fat_g=_f(row.fat_g), fiber_g=_f(row.fiber_g), latest_price=_f(row.latest_price),
        price_unit=row.price_unit, latest_price_per_unit=_f(row.latest_price_per_unit),
    )


class SqlIngredientRepository(IngredientRepositoryPort):
    """Đọc qua view v_ingredients_full (đã join dinh dưỡng + giá mới nhất);
    ghi qua ORM (IngredientModel, NutritionFactsModel)."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_full(self, food_group, search, active_only, limit, offset) -> list[IngredientFullEntity]:
        sql = "SELECT * FROM v_ingredients_full WHERE 1=1"
        params: dict = {}
        if active_only:
            sql += " AND is_active = TRUE"
        if food_group:
            sql += " AND food_group = :fg"
            params["fg"] = food_group
        if search:
            sql += " AND name ILIKE :kw"
            params["kw"] = f"%{search}%"
        sql += " ORDER BY name LIMIT :limit OFFSET :offset"
        params["limit"] = limit
        params["offset"] = offset
        rows = self._session.execute(text(sql), params).fetchall()
        return [_full_from_row(r) for r in rows]

    def get_full(self, ingredient_id: int) -> IngredientFullEntity | None:
        row = self._session.execute(
            text("SELECT * FROM v_ingredients_full WHERE id = :id"), {"id": ingredient_id}
        ).first()
        return _full_from_row(row) if row else None

    def get_by_name(self, name: str) -> IngredientEntity | None:
        row = self._session.exec(select(IngredientModel).where(IngredientModel.name == name)).first()
        return _to_entity(row) if row else None

    def get(self, ingredient_id: int) -> IngredientEntity | None:
        row = self._session.get(IngredientModel, ingredient_id)
        return _to_entity(row) if row else None

    def create(self, ingredient: IngredientEntity, nutrition: NutritionFactsEntity) -> IngredientEntity:
        row = IngredientModel(
            name=ingredient.name, food_group=ingredient.food_group,
            default_unit=ingredient.default_unit, grams_per_unit=ingredient.grams_per_unit,
        )
        self._session.add(row)
        self._session.commit()
        self._session.refresh(row)
        nf_row = NutritionFactsModel(ingredient_id=row.id, calories=nutrition.calories,
                                      protein_g=nutrition.protein_g, carbs_g=nutrition.carbs_g,
                                      fat_g=nutrition.fat_g, fiber_g=nutrition.fiber_g)
        self._session.add(nf_row)
        self._session.commit()
        return _to_entity(row)

    def save(self, ingredient: IngredientEntity) -> IngredientEntity:
        row = self._session.get(IngredientModel, ingredient.id)
        row.name = ingredient.name
        row.food_group = ingredient.food_group
        row.default_unit = ingredient.default_unit
        row.grams_per_unit = ingredient.grams_per_unit
        row.is_active = ingredient.is_active
        self._session.add(row)
        self._session.commit()
        self._session.refresh(row)
        return _to_entity(row)

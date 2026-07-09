# File: backend/app/modules/admin/router.py
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session, select, func

from app.core.database import get_session
from app.core.deps import require_admin
from app.modules.identity.domain import UserEntity
from app.modules.identity.models import UserModel
from app.modules.ingredients.models import IngredientModel, NutritionFactsModel
from app.modules.meals.models import MealModel, MealIngredientModel

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/stats")
def get_stats(
    session: Session = Depends(get_session),
    _: UserEntity = Depends(require_admin),
):
    """Tổng quan số liệu cho dashboard admin."""
    total_users = session.exec(select(func.count()).select_from(UserModel)).one()
    total_ingredients = session.exec(
        select(func.count()).select_from(IngredientModel).where(IngredientModel.is_active == True)
    ).one()
    total_meals = session.exec(
        select(func.count()).select_from(MealModel).where(MealModel.is_active == True)
    ).one()

    # Nguyên liệu có dinh dưỡng
    ing_with_nutrition = session.exec(
        select(func.count(func.distinct(NutritionFactsModel.ingredient_id)))
    ).one()
    ing_missing_nutrition = max(0, total_ingredients - ing_with_nutrition)

    # Món có nguyên liệu
    meal_with_ing = session.exec(
        select(func.count(func.distinct(MealIngredientModel.meal_id)))
    ).one()
    meal_missing_ing = max(0, total_meals - meal_with_ing)

    return {
        "total_users": total_users,
        "total_ingredients": total_ingredients,
        "total_meals": total_meals,
        "ingredients_missing_nutrition": ing_missing_nutrition,
        "ingredients_missing_price": 0,  # chưa nối, cần xem PriceSnapshotModel ở đâu
        "meals_missing_ingredients": meal_missing_ing,
    }
# File: backend/app/api.py
# Gom router của các module đã triển khai. Module chưa có router (nutrition
# không expose HTTP riêng; shopping_lists/admin/ai chưa triển khai) sẽ được
# include khi sẵn sàng.
from __future__ import annotations

from fastapi import APIRouter

from app.modules.identity.router import router as identity_router
from app.modules.ingredients.router import router as ingredients_router
from app.modules.meal_planning.router import router as meal_planning_router
from app.modules.meals.router import router as meals_router
from app.modules.profiles.router import router as profiles_router

api_router = APIRouter()
api_router.include_router(identity_router)
api_router.include_router(profiles_router)
api_router.include_router(ingredients_router)
api_router.include_router(meals_router)
api_router.include_router(meal_planning_router)

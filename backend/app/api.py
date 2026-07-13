# Gom router của các module đã triển khai.
from __future__ import annotations

from fastapi import APIRouter

from app.modules.ai.router import router as ai_router
from app.modules.ai.admin_router import router as ai_admin_router
from app.modules.admin.router import router as admin_router
from app.modules.dishes.router import router as dishes_router
from app.modules.identity.router import auth_router, router as users_router
from app.modules.ingredients.router import router as ingredients_router
from app.modules.meal_planning.router import router as meal_planning_router
from app.modules.meals.router import router as meals_router
from app.modules.nutrition.router import router as nutrition_router
from app.modules.profiles.router import router as profiles_router
from app.modules.shopping_lists.router import public_router as public_shopping_lists_router, router as shopping_lists_router
from app.modules.tags.router import admin_router as admin_tags_router, router as tags_router

api_router = APIRouter()
api_router.include_router(auth_router)        # /api/auth/*
api_router.include_router(users_router)       # /api/users/*
api_router.include_router(profiles_router)    # /api/profiles/*
api_router.include_router(ingredients_router)
api_router.include_router(dishes_router)
api_router.include_router(meals_router)
api_router.include_router(meal_planning_router)
api_router.include_router(shopping_lists_router)
api_router.include_router(public_shopping_lists_router)
api_router.include_router(tags_router)
api_router.include_router(admin_tags_router)
api_router.include_router(nutrition_router)   # /api/nutrition/*
api_router.include_router(ai_router)          # /api/ai/*
api_router.include_router(ai_admin_router)    # /api/admin/ai/*
api_router.include_router(admin_router)       # /api/admin/*

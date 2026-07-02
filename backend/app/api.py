# File: backend/app/api.py
# Gom router của các module đã triển khai.
from __future__ import annotations

from fastapi import APIRouter

from app.modules.identity.router import auth_router, router as users_router
from app.modules.ingredients.router import router as ingredients_router
from app.modules.meal_planning.router import router as meal_planning_router
from app.modules.meals.router import router as meals_router
from app.modules.profiles.router import router as profiles_router

api_router = APIRouter()
api_router.include_router(auth_router)        # /api/auth/*
api_router.include_router(users_router)       # /api/users/*
api_router.include_router(profiles_router)    # /api/profiles/*
api_router.include_router(ingredients_router)
api_router.include_router(meals_router)
api_router.include_router(meal_planning_router)
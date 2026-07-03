# File: backend/app/dependencies.py
# Composition root: nối use case với repository qua FastAPI Depends().
from __future__ import annotations

from fastapi import Depends
from sqlmodel import Session

from app.core.database import get_session

# ── identity ──────────────────────────────────────────────────────────────
from app.modules.identity.repository import SqlUserRepository
from app.modules.identity.use_cases import (
    CreateUserUseCase, DeleteUserUseCase, GetUserUseCase,
    ListUsersUseCase, LoginUseCase, UpdateUserUseCase,
)


def get_list_users_use_case(s: Session = Depends(get_session)) -> ListUsersUseCase:
    return ListUsersUseCase(SqlUserRepository(s))

def get_get_user_use_case(s: Session = Depends(get_session)) -> GetUserUseCase:
    return GetUserUseCase(SqlUserRepository(s))

def get_create_user_use_case(s: Session = Depends(get_session)) -> CreateUserUseCase:
    return CreateUserUseCase(SqlUserRepository(s))

def get_update_user_use_case(s: Session = Depends(get_session)) -> UpdateUserUseCase:
    return UpdateUserUseCase(SqlUserRepository(s))

def get_delete_user_use_case(s: Session = Depends(get_session)) -> DeleteUserUseCase:
    return DeleteUserUseCase(SqlUserRepository(s))

def get_login_use_case(s: Session = Depends(get_session)) -> LoginUseCase:
    return LoginUseCase(SqlUserRepository(s))


# ── profiles ──────────────────────────────────────────────────────────────
from app.modules.profiles.repository import SqlExclusionRepository, SqlUserProfileRepository
from app.modules.profiles.use_cases import (
    AddExclusionUseCase, CreateEmptyProfileUseCase, GetProfileUseCase, ListExclusionsUseCase,
    RemoveExclusionUseCase, UpdateProfileUseCase,
)


def get_create_empty_profile_use_case(s: Session = Depends(get_session)) -> CreateEmptyProfileUseCase:
    return CreateEmptyProfileUseCase(SqlUserProfileRepository(s))

def get_get_profile_use_case(s: Session = Depends(get_session)) -> GetProfileUseCase:
    return GetProfileUseCase(SqlUserProfileRepository(s))

def get_update_profile_use_case(s: Session = Depends(get_session)) -> UpdateProfileUseCase:
    return UpdateProfileUseCase(SqlUserProfileRepository(s))

def get_list_exclusions_use_case(s: Session = Depends(get_session)) -> ListExclusionsUseCase:
    return ListExclusionsUseCase(SqlExclusionRepository(s))

def get_add_exclusion_use_case(s: Session = Depends(get_session)) -> AddExclusionUseCase:
    return AddExclusionUseCase(SqlExclusionRepository(s))

def get_remove_exclusion_use_case(s: Session = Depends(get_session)) -> RemoveExclusionUseCase:
    return RemoveExclusionUseCase(SqlExclusionRepository(s))


# ── ingredients ───────────────────────────────────────────────────────────
from app.modules.ingredients.repository import SqlIngredientRepository
from app.modules.ingredients.use_cases import (
    CreateIngredientUseCase, DeactivateIngredientUseCase, GetIngredientUseCase,
    ListIngredientsUseCase, UpdateIngredientUseCase,
)


def get_list_ingredients_use_case(s: Session = Depends(get_session)) -> ListIngredientsUseCase:
    return ListIngredientsUseCase(SqlIngredientRepository(s))

def get_get_ingredient_use_case(s: Session = Depends(get_session)) -> GetIngredientUseCase:
    return GetIngredientUseCase(SqlIngredientRepository(s))

def get_create_ingredient_use_case(s: Session = Depends(get_session)) -> CreateIngredientUseCase:
    return CreateIngredientUseCase(SqlIngredientRepository(s))

def get_update_ingredient_use_case(s: Session = Depends(get_session)) -> UpdateIngredientUseCase:
    return UpdateIngredientUseCase(SqlIngredientRepository(s))

def get_deactivate_ingredient_use_case(s: Session = Depends(get_session)) -> DeactivateIngredientUseCase:
    return DeactivateIngredientUseCase(SqlIngredientRepository(s))


# ── meals ─────────────────────────────────────────────────────────────────
from app.modules.meals.repository import SqlMealRepository
from app.modules.meals.use_cases import (
    CreateMealUseCase, DeactivateMealUseCase, GetMealUseCase, ListMealsUseCase, UpdateMealUseCase,
)


def get_list_meals_use_case(s: Session = Depends(get_session)) -> ListMealsUseCase:
    return ListMealsUseCase(SqlMealRepository(s))

def get_get_meal_use_case(s: Session = Depends(get_session)) -> GetMealUseCase:
    return GetMealUseCase(SqlMealRepository(s))

def get_create_meal_use_case(s: Session = Depends(get_session)) -> CreateMealUseCase:
    return CreateMealUseCase(SqlMealRepository(s))

def get_update_meal_use_case(s: Session = Depends(get_session)) -> UpdateMealUseCase:
    return UpdateMealUseCase(SqlMealRepository(s))

def get_deactivate_meal_use_case(s: Session = Depends(get_session)) -> DeactivateMealUseCase:
    return DeactivateMealUseCase(SqlMealRepository(s))


# ── meal_planning ─────────────────────────────────────────────────────────
# NOTE: phần sinh thực đơn tự động (Generate/BuildPlanRequest + candidate provider)
# là code của Đức, merge từ main. Giữ nguyên, không xoá.
from app.modules.meal_planning.candidate_repository import SqlMealCandidateProvider
from app.modules.meal_planning.repository import SqlMealPlanRepository
from app.modules.meal_planning.use_cases import (
    BuildPlanRequestUseCase, DeleteMealPlanUseCase, GenerateMealPlanUseCase, GetMealPlanUseCase,
    ListMealPlansUseCase, SaveMealPlanUseCase,
)


def get_save_meal_plan_use_case(s: Session = Depends(get_session)) -> SaveMealPlanUseCase:
    return SaveMealPlanUseCase(SqlMealPlanRepository(s))

def get_list_meal_plans_use_case(s: Session = Depends(get_session)) -> ListMealPlansUseCase:
    return ListMealPlansUseCase(SqlMealPlanRepository(s))

def get_get_meal_plan_use_case(s: Session = Depends(get_session)) -> GetMealPlanUseCase:
    return GetMealPlanUseCase(SqlMealPlanRepository(s))

def get_delete_meal_plan_use_case(s: Session = Depends(get_session)) -> DeleteMealPlanUseCase:
    return DeleteMealPlanUseCase(SqlMealPlanRepository(s))

def get_generate_meal_plan_use_case(s: Session = Depends(get_session)) -> GenerateMealPlanUseCase:
    return GenerateMealPlanUseCase(SqlMealCandidateProvider(s))

def get_build_plan_request_use_case(s: Session = Depends(get_session)) -> BuildPlanRequestUseCase:
    return BuildPlanRequestUseCase(SqlUserProfileRepository(s), SqlExclusionRepository(s))
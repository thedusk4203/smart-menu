# Composition root: nối use case với repository qua FastAPI Depends().
from __future__ import annotations

from fastapi import Depends
from sqlalchemy import text
from sqlmodel import Session

from app.core.database import get_ai_context_session, get_ai_state_session, get_session
from app.core.deps import get_current_user
# ── identity ──────────────────────────────────────────────────────────────
from app.modules.identity.repository import SqlUserRepository
from app.modules.identity.use_cases import (
    CreateUserUseCase, DeleteUserUseCase, GetUserUseCase,
    GoogleLoginUseCase, ListUsersUseCase, LoginUseCase, UpdateUserUseCase,
)
from app.modules.identity.google_verifier import GoogleTokenVerifier


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


def get_google_login_use_case(s: Session = Depends(get_session)) -> GoogleLoginUseCase:
    return GoogleLoginUseCase(SqlUserRepository(s), GoogleTokenVerifier())


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
from app.modules.meal_planning.dish_candidate_repository import SqlDishCandidateProvider
from app.modules.meal_planning.repository import SqlMealPlanRepository
from app.modules.meal_planning.unit_of_work import SqlMealPlanUnitOfWork
from app.modules.inventory.repository import SqlInventoryRepository
from app.modules.inventory.unit_of_work import SqlInventoryUnitOfWork
from app.modules.inventory.use_cases import ListInventoryLotsUseCase, UpdateInventoryLotUseCase
from app.modules.meal_planning.use_cases import (
    BuildPlanRequestUseCase, DeleteMealPlanUseCase, GenerateMealPlanUseCase, GetMealPlanUseCase,
    ListMealPlansUseCase, SaveMealPlanUseCase,
)


def get_save_meal_plan_use_case(s: Session = Depends(get_session)) -> SaveMealPlanUseCase:
    return SaveMealPlanUseCase(
        SqlMealPlanUnitOfWork(s),
        SqlDishCandidateProvider(s),
        BuildPlanRequestUseCase(
            SqlUserProfileRepository(s), SqlExclusionRepository(s), SqlInventoryRepository(s)
        ),
    )

def get_list_meal_plans_use_case(s: Session = Depends(get_session)) -> ListMealPlansUseCase:
    return ListMealPlansUseCase(SqlMealPlanRepository(s))

def get_get_meal_plan_use_case(s: Session = Depends(get_session)) -> GetMealPlanUseCase:
    return GetMealPlanUseCase(SqlMealPlanRepository(s))

def get_delete_meal_plan_use_case(s: Session = Depends(get_session)) -> DeleteMealPlanUseCase:
    return DeleteMealPlanUseCase(SqlMealPlanUnitOfWork(s))

def get_generate_meal_plan_use_case(s: Session = Depends(get_session)) -> GenerateMealPlanUseCase:
    return GenerateMealPlanUseCase(SqlDishCandidateProvider(s))

def get_build_plan_request_use_case(s: Session = Depends(get_session)) -> BuildPlanRequestUseCase:
    return BuildPlanRequestUseCase(
        SqlUserProfileRepository(s), SqlExclusionRepository(s), SqlInventoryRepository(s)
    )


def get_list_inventory_lots_use_case(
    s: Session = Depends(get_session),
) -> ListInventoryLotsUseCase:
    return ListInventoryLotsUseCase(SqlInventoryRepository(s))


def get_update_inventory_lot_use_case(
    s: Session = Depends(get_session),
) -> UpdateInventoryLotUseCase:
    return UpdateInventoryLotUseCase(SqlInventoryUnitOfWork(s))


# ── shopping lists ────────────────────────────────────────────────────────
from app.modules.shopping_lists.repository import SqlShoppingShareRepository
from app.modules.shopping_lists.unit_of_work import SqlShoppingListUnitOfWork
from app.modules.shopping_lists.use_cases import (
    BuildShoppingListUseCase,
    GetActiveShoppingShareUseCase,
    GetOrCreateShoppingShareUseCase,
    RevokeShoppingShareUseCase,
    UpdateShoppingItemUseCase,
    UpdateShoppingItemsUseCase,
)


def get_build_shopping_list_use_case(s: Session = Depends(get_session)) -> BuildShoppingListUseCase:
    return BuildShoppingListUseCase(SqlShoppingListUnitOfWork(s))


def get_update_shopping_item_use_case(
    s: Session = Depends(get_session),
) -> UpdateShoppingItemUseCase:
    return UpdateShoppingItemUseCase(SqlShoppingListUnitOfWork(s))


def get_update_shopping_items_use_case(
    s: Session = Depends(get_session),
) -> UpdateShoppingItemsUseCase:
    return UpdateShoppingItemsUseCase(SqlShoppingListUnitOfWork(s))


def get_or_create_shopping_share_use_case(
    s: Session = Depends(get_session),
) -> GetOrCreateShoppingShareUseCase:
    return GetOrCreateShoppingShareUseCase(SqlShoppingListUnitOfWork(s))


def get_active_shopping_share_use_case(
    s: Session = Depends(get_session),
) -> GetActiveShoppingShareUseCase:
    return GetActiveShoppingShareUseCase(SqlShoppingShareRepository(s))


def get_revoke_shopping_share_use_case(
    s: Session = Depends(get_session),
) -> RevokeShoppingShareUseCase:
    return RevokeShoppingShareUseCase(SqlShoppingListUnitOfWork(s))


# ── nutrition ─────────────────────────────────────────────────────────────
from app.modules.nutrition.use_cases import CalculateNutritionTargetUseCase


def get_calculate_nutrition_target_use_case() -> CalculateNutritionTargetUseCase:
    return CalculateNutritionTargetUseCase()


# ── ai ────────────────────────────────────────────────────────────────────
from app.modules.ai.client import DisabledAIClient, LoggedAIClient, OpenAICompatibleAIClient
from app.modules.ai.conversation_store import ConversationStore
from app.modules.ai.ports import AIClientPort
from app.modules.ai.personalization import AIContextReader, AIPreferenceStore, ActiveDishTagReader
from app.modules.ai.prompt_store import SystemPromptStore
from app.modules.ai.provider_store import AIRequestLogStore, ProviderConfigStore
from app.modules.identity.domain import UserEntity
from app.modules.ai.use_cases import (
    ChatUseCase,
    ConversationHistoryUseCase,
    ExplainPlanUseCase,
    ParseMenuRequestUseCase,
    SuggestSwapUseCase,
)


def _get_ai_client(
    config_session: Session,
    state_session: Session,
    user: UserEntity,
    feature: str,
) -> AIClientPort:
    config = ProviderConfigStore(config_session).active()
    if config is None:
        return DisabledAIClient()
    client = OpenAICompatibleAIClient(
        base_url=config.base_url,
        model=config.model,
        api_key=config.api_key,
        timeout_seconds=config.timeout_seconds,
        structured_output_mode=config.structured_output_mode or "json_schema",
        native_web_search_enabled=config.native_web_search_enabled,
    )
    return LoggedAIClient(
        client,
        AIRequestLogStore(state_session, actor_id=user.id),
        config,
        user_id=user.id,
        feature=feature,
    )


def get_ai_chat_use_case(
    s: Session = Depends(get_session),
    context_s: Session = Depends(get_ai_context_session),
    state_s: Session = Depends(get_ai_state_session),
    user: UserEntity = Depends(get_current_user),
) -> ChatUseCase:
    return ChatUseCase(
        _get_ai_client(s, state_s, user, "chat"),
        ConversationStore(state_s, actor_id=user.id),
        SystemPromptStore(s).get_effective("chat"),
        context_reader=AIContextReader(context_s),
        preferences=AIPreferenceStore(state_s),
    )


def get_ai_conversation_history_use_case(
    s: Session = Depends(get_ai_state_session),
    user: UserEntity = Depends(get_current_user),
) -> ConversationHistoryUseCase:
    return ConversationHistoryUseCase(ConversationStore(s, actor_id=user.id))


def get_ai_parse_menu_request_use_case(
    s: Session = Depends(get_session),
    context_s: Session = Depends(get_ai_context_session),
    state_s: Session = Depends(get_ai_state_session),
    user: UserEntity = Depends(get_current_user),
) -> ParseMenuRequestUseCase:
    return ParseMenuRequestUseCase(
        _get_ai_client(s, state_s, user, "parse_menu"),
        SystemPromptStore(s).get_effective("parse_menu"),
        tags=ActiveDishTagReader(context_s),
    )


def get_ai_explain_plan_use_case(
    s: Session = Depends(get_session),
    state_s: Session = Depends(get_ai_state_session),
    user: UserEntity = Depends(get_current_user),
) -> ExplainPlanUseCase:
    return ExplainPlanUseCase(
        _get_ai_client(s, state_s, user, "explain_plan"),
        SystemPromptStore(s).get_effective("explain_plan"),
    )


def get_ai_suggest_swap_use_case(
    s: Session = Depends(get_session),
    context_s: Session = Depends(get_ai_context_session),
    state_s: Session = Depends(get_ai_state_session),
    user: UserEntity = Depends(get_current_user),
) -> SuggestSwapUseCase:
    context_s.execute(
        text("SELECT set_config('app.current_user_id', :actor_id, true)"),
        {"actor_id": str(user.id)},
    )
    return SuggestSwapUseCase(
        _get_ai_client(s, state_s, user, "suggest_swap"),
        SqlDishCandidateProvider(context_s),
        BuildPlanRequestUseCase(
            SqlUserProfileRepository(context_s), SqlExclusionRepository(context_s),
            SqlInventoryRepository(context_s)
        ),
        SystemPromptStore(s).get_effective("suggest_swap"),
    )

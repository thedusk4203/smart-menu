# File: backend/app/modules/ai/router.py
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.deps import get_current_user
from app.dependencies import (
    get_ai_chat_use_case,
    get_ai_explain_plan_use_case,
    get_ai_parse_menu_request_use_case,
    get_ai_suggest_swap_use_case,
)
from app.modules.ai.schemas import (
    ChatRequest,
    ChatResponse,
    ExplainPlanRequest,
    ParsedMenuRequest,
    ParseMenuRequest,
    SwapSuggestion,
    SwapSuggestionRequest,
)
from app.modules.ai.use_cases import (
    ChatUseCase,
    ExplainPlanUseCase,
    ParseMenuRequestUseCase,
    SuggestSwapUseCase,
)
from app.modules.identity.domain import UserEntity

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/chat", response_model=ChatResponse)
def chat(
    data: ChatRequest,
    current_user: UserEntity = Depends(get_current_user),
    use_case: ChatUseCase = Depends(get_ai_chat_use_case),
):
    return use_case.execute(data)


@router.post("/parse-menu-request", response_model=ParsedMenuRequest)
def parse_menu_request(
    data: ParseMenuRequest,
    current_user: UserEntity = Depends(get_current_user),
    use_case: ParseMenuRequestUseCase = Depends(get_ai_parse_menu_request_use_case),
):
    return use_case.execute(data)


@router.post("/explain-plan", response_model=ChatResponse)
def explain_plan(
    data: ExplainPlanRequest,
    current_user: UserEntity = Depends(get_current_user),
    use_case: ExplainPlanUseCase = Depends(get_ai_explain_plan_use_case),
):
    return use_case.execute(data)


@router.post("/suggest-swap", response_model=list[SwapSuggestion])
def suggest_swap(
    data: SwapSuggestionRequest,
    current_user: UserEntity = Depends(get_current_user),
    use_case: SuggestSwapUseCase = Depends(get_ai_suggest_swap_use_case),
):
    return use_case.execute(data)

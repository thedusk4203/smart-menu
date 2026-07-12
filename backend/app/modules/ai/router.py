from __future__ import annotations

import json
from collections.abc import Iterator

from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from sqlmodel import Session

from app.core.deps import get_current_user
from app.core.database import get_session
from app.dependencies import (
    get_ai_chat_use_case,
    get_ai_conversation_history_use_case,
    get_ai_explain_plan_use_case,
    get_ai_parse_menu_request_use_case,
    get_ai_suggest_swap_use_case,
)
from app.modules.ai.schemas import (
    ChatRequest,
    ChatResponse,
    ConversationChatResponse,
    ConversationDetail,
    ConversationSummary,
    ExplainPlanRequest,
    ParsedMenuRequest,
    ParseMenuRequest,
    SwapSuggestion,
    SwapSuggestionRequest,
)
from app.modules.ai.use_cases import (
    ChatUseCase,
    ConversationHistoryUseCase,
    ExplainPlanUseCase,
    ParseMenuRequestUseCase,
    SuggestSwapUseCase,
)
from app.modules.identity.domain import UserEntity
from app.modules.ai.admin_schemas import AIStatus
from app.modules.ai.provider_store import ProviderConfigStore

router = APIRouter(prefix="/api/ai", tags=["ai"])


def _encode_sse(events: Iterator[dict]) -> Iterator[str]:
    for event in events:
        payload = json.dumps(event["data"], ensure_ascii=False, separators=(",", ":"))
        yield f"event: {event['event']}\ndata: {payload}\n\n"


def _stream_response(events: Iterator[dict]) -> StreamingResponse:
    return StreamingResponse(
        _encode_sse(events),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/status", response_model=AIStatus)
def ai_status(session: Session = Depends(get_session),
              _: UserEntity = Depends(get_current_user)):
    config = ProviderConfigStore(session).active()
    if config is None:
        return AIStatus(enabled=False, features=[])
    return AIStatus(enabled=True, source=config.source, provider_name=config.name,
                    provider_type=config.provider_type, model=config.model,
                    features=["chat", "parse_menu", "explain_plan", "suggest_swap"])


@router.post("/chat", responses={200: {"content": {"text/event-stream": {}}}})
def chat(
    data: ChatRequest,
    current_user: UserEntity = Depends(get_current_user),
    use_case: ChatUseCase = Depends(get_ai_chat_use_case),
):
    stream = use_case.open_chat_stream(data, user_id=current_user.id)
    return _stream_response(stream.events())


@router.get("/conversations", response_model=list[ConversationSummary])
def list_conversations(
    current_user: UserEntity = Depends(get_current_user),
    use_case: ConversationHistoryUseCase = Depends(
        get_ai_conversation_history_use_case
    ),
):
    return use_case.list(user_id=current_user.id)


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
def get_conversation(
    conversation_id: int,
    current_user: UserEntity = Depends(get_current_user),
    use_case: ConversationHistoryUseCase = Depends(
        get_ai_conversation_history_use_case
    ),
):
    return use_case.get(conversation_id=conversation_id, user_id=current_user.id)


@router.delete(
    "/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_conversation(
    conversation_id: int,
    current_user: UserEntity = Depends(get_current_user),
    use_case: ConversationHistoryUseCase = Depends(
        get_ai_conversation_history_use_case
    ),
):
    use_case.delete(conversation_id=conversation_id, user_id=current_user.id)


@router.post(
    "/conversations/{conversation_id}/turns/{turn_id}/retry",
    responses={200: {"content": {"text/event-stream": {}}}},
)
def retry_conversation_turn(
    conversation_id: int,
    turn_id: int,
    current_user: UserEntity = Depends(get_current_user),
    use_case: ChatUseCase = Depends(get_ai_chat_use_case),
):
    stream = use_case.open_retry_stream(
        conversation_id=conversation_id,
        turn_id=turn_id,
        user_id=current_user.id,
    )
    return _stream_response(stream.events())


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
    return use_case.execute(data, user_id=current_user.id)

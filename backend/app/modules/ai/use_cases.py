# File: backend/app/modules/ai/use_cases.py
from __future__ import annotations

import json
from typing import Any

from pydantic import ValidationError

from app.modules.ai.exceptions import AIResponseValidationError, AIUnavailableError
from app.modules.ai.ports import AIClientPort
from app.modules.ai.prompts import (
    CHAT_SYSTEM_PROMPT,
    EXPLAIN_PLAN_SYSTEM_PROMPT,
    PARSE_MENU_SYSTEM_PROMPT,
)
from app.modules.ai.schemas import (
    ChatRequest,
    ChatResponse,
    ExplainPlanRequest,
    ParsedMenuRequest,
    ParseMenuRequest,
    SwapSuggestionRequest,
)


class ChatUseCase:
    def __init__(self, client: AIClientPort) -> None:
        self._client = client

    def execute(self, data: ChatRequest) -> ChatResponse:
        user_content = data.message
        if data.context is not None:
            user_content += "\n\nNgữ cảnh ứng dụng:\n" + _compact_json(data.context)

        reply = self._client.complete_text(
            [
                {"role": "system", "content": CHAT_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.4,
            max_tokens=700,
        )
        return ChatResponse(reply=reply)


class ParseMenuRequestUseCase:
    def __init__(self, client: AIClientPort) -> None:
        self._client = client

    def execute(self, data: ParseMenuRequest) -> ParsedMenuRequest:
        raw = self._client.complete_json(
            [
                {"role": "system", "content": PARSE_MENU_SYSTEM_PROMPT},
                {"role": "user", "content": data.message},
            ],
            schema_name="smart_menu_plan_request",
            json_schema=ParsedMenuRequest.model_json_schema(),
            temperature=0.1,
            max_tokens=500,
        )
        try:
            return ParsedMenuRequest.model_validate(raw)
        except ValidationError as exc:
            raise AIResponseValidationError("AI parse request không khớp schema.") from exc


class ExplainPlanUseCase:
    def __init__(self, client: AIClientPort) -> None:
        self._client = client

    def execute(self, data: ExplainPlanRequest) -> ChatResponse:
        payload = {
            "plan_data": data.plan_data,
            "total_cost": data.total_cost,
            "total_calories": data.total_calories,
            "budget_limit": data.budget_limit,
        }
        reply = self._client.complete_text(
            [
                {"role": "system", "content": EXPLAIN_PLAN_SYSTEM_PROMPT},
                {"role": "user", "content": _compact_json(payload, limit=12000)},
            ],
            temperature=0.3,
            max_tokens=900,
        )
        return ChatResponse(reply=reply)


class SuggestSwapUseCase:
    def __init__(self, client: AIClientPort) -> None:
        self._client = client

    def execute(self, data: SwapSuggestionRequest) -> list:
        raise AIUnavailableError(
            "Đổi món bằng AI cần danh sách candidate hợp lệ và bước validate lại trước khi bật."
        )


def _compact_json(data: Any, *, limit: int = 5000) -> str:
    text = json.dumps(data, ensure_ascii=False, default=str)
    if len(text) <= limit:
        return text
    return text[:limit] + "... [truncated]"

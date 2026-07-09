from __future__ import annotations

import pytest

from app.modules.ai.exceptions import AIResponseValidationError
from app.modules.ai.ports import AIClientPort, AIMessage
from app.modules.ai.schemas import ChatRequest, ParseMenuRequest
from app.modules.ai.use_cases import ChatUseCase, ParseMenuRequestUseCase


class _FakeAIClient(AIClientPort):
    def __init__(self, *, text: str = "ok", json_data=None) -> None:
        self.text = text
        self.json_data = json_data if json_data is not None else {}
        self.messages: list[AIMessage] | None = None

    def complete_text(
        self,
        messages: list[AIMessage],
        *,
        temperature: float = 0.4,
        max_tokens: int = 700,
    ) -> str:
        self.messages = messages
        return self.text

    def complete_json(
        self,
        messages: list[AIMessage],
        *,
        schema_name: str,
        json_schema: dict,
        temperature: float = 0.1,
        max_tokens: int = 700,
    ) -> dict:
        self.messages = messages
        return self.json_data


def test_chat_use_case_returns_ai_reply():
    client = _FakeAIClient(text="Chào bạn")
    result = ChatUseCase(client).execute(ChatRequest(message="Xin chào"))

    assert result.reply == "Chào bạn"
    assert client.messages is not None
    assert client.messages[0]["role"] == "system"


def test_parse_menu_request_validates_structured_output():
    client = _FakeAIClient(
        json_data={
            "days": 7,
            "meals_per_day": 3,
            "budget_limit": 500000,
            "preferred_tags": ["healthy", "ít dầu mỡ"],
            "needs_clarification": False,
            "clarification_question": None,
        }
    )

    result = ParseMenuRequestUseCase(client).execute(
        ParseMenuRequest(message="7 ngày 3 bữa ngân sách 500k")
    )

    assert result.days == 7
    assert result.meals_per_day == 3
    assert result.budget_limit == 500000
    assert result.preferred_tags == ["healthy", "ít dầu mỡ"]


def test_parse_menu_request_rejects_invalid_ai_shape():
    client = _FakeAIClient(json_data={"days": 99})

    with pytest.raises(AIResponseValidationError):
        ParseMenuRequestUseCase(client).execute(ParseMenuRequest(message="99 ngày"))

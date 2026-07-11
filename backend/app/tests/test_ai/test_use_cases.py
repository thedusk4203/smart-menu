from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.modules.ai.exceptions import AIResponseValidationError, AIUnavailableError
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
    ) -> str:
        self.messages = messages
        return self.text

    def stream_text(self, messages: list[AIMessage]):
        self.messages = messages
        yield self.text

    def complete_json(
        self,
        messages: list[AIMessage],
        *,
        schema_name: str,
        json_schema: dict,
    ) -> dict:
        self.messages = messages
        return self.json_data


class _UnavailableAIClient(_FakeAIClient):
    def complete_json(self, messages, *, schema_name, json_schema):
        raise AIUnavailableError("provider unavailable")


class _FakeConversationStore:
    def __init__(self) -> None:
        self.failed = False

    def start_turn(self, *, user_id, message, conversation_id):
        now = datetime.now(timezone.utc)
        return 9, {
            "id": 11,
            "turn_number": 1,
            "user_content": message,
            "assistant_content": None,
            "status": "pending",
            "created_at": now,
            "updated_at": now,
        }

    def completed_turns_before(self, *, conversation_id, turn_number):
        return []

    def complete_turn(self, *, conversation_id, turn_id, assistant_content):
        now = datetime.now(timezone.utc)
        return {
            "id": turn_id,
            "turn_number": 1,
            "user_content": "Xin chào",
            "assistant_content": assistant_content,
            "status": "completed",
            "created_at": now,
            "updated_at": now,
        }

    def fail_turn(self, **kwargs):
        self.failed = True


def test_chat_stream_returns_deltas_then_completes_turn():
    client = _FakeAIClient(text="Chào bạn")
    events = list(ChatUseCase(client, _FakeConversationStore()).open_chat_stream(
        ChatRequest(message="Xin chào"), user_id=1
    ).events())

    assert [event["event"] for event in events] == ["start", "delta", "done"]
    assert events[-1]["data"]["reply"] == "Chào bạn"
    assert events[-1]["data"]["conversation_id"] == 9
    assert events[-1]["data"]["turn"]["status"] == "completed"
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


def test_parse_menu_request_uses_deterministic_fields_when_llm_only_clarifies():
    client = _FakeAIClient(json_data={
        "needs_clarification": True,
        "clarification_question": "Bạn có thích ăn chay không?",
    })

    result = ParseMenuRequestUseCase(client).execute(
        ParseMenuRequest(message="thực đơn 4 ngày, ngân sách 600k. 2 bữa một ngày")
    )

    assert result.days == 4
    assert result.meals_per_day == 2
    assert result.budget_limit == 600_000
    assert result.needs_clarification is False
    assert result.clarification_question is None


def test_parse_menu_request_deterministic_values_override_llm_values():
    client = _FakeAIClient(json_data={
        "days": 7,
        "meals_per_day": 3,
        "budget_limit": 100_000,
        "preferred_tags": ["giàu đạm"],
    })

    result = ParseMenuRequestUseCase(client).execute(
        ParseMenuRequest(message="4 ngày, 2 bữa, ngân sách 600 nghìn, ưu tiên giàu đạm")
    )

    assert (result.days, result.meals_per_day, result.budget_limit) == (4, 2, 600_000)
    assert result.preferred_tags == ["giàu đạm"]
    assert result.needs_clarification is False


def test_parse_menu_request_falls_back_when_llm_is_unavailable():
    result = ParseMenuRequestUseCase(_UnavailableAIClient()).execute(
        ParseMenuRequest(message="3 ngày, ngân sách 450k, mỗi ngày 2 bữa")
    )

    assert (result.days, result.meals_per_day, result.budget_limit) == (3, 2, 450_000)
    assert result.preferred_tags == []
    assert result.needs_clarification is False


def test_parse_menu_request_falls_back_when_llm_shape_is_invalid_but_numbers_are_valid():
    result = ParseMenuRequestUseCase(_FakeAIClient(json_data={"days": 99})).execute(
        ParseMenuRequest(message="5 ngày, 3 bữa, ngân sách 1 triệu")
    )

    assert (result.days, result.meals_per_day, result.budget_limit) == (5, 3, 1_000_000)
    assert result.needs_clarification is False


def test_parse_menu_request_only_clarifies_when_nothing_is_actionable():
    result = ParseMenuRequestUseCase(_FakeAIClient(json_data={})).execute(
        ParseMenuRequest(message="tạo giúp tôi một thực đơn")
    )

    assert result.needs_clarification is True
    assert result.clarification_question

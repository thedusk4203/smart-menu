from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import text

from app.core.exceptions import ConflictError, NotFoundError
from app.modules.ai.conversation_store import ConversationStore, make_conversation_title
from app.modules.ai.exceptions import AIResponseValidationError, AIUnavailableError
from app.modules.ai.schemas import ChatRequest
from app.modules.ai.use_cases import ChatUseCase, _recent_chat_history


def _turn(number: int, user: str = "user", assistant: str = "assistant"):
    now = datetime.now(timezone.utc)
    return {
        "id": number,
        "turn_number": number,
        "user_content": f"{user}-{number}",
        "assistant_content": f"{assistant}-{number}",
        "status": "completed",
        "created_at": now,
        "updated_at": now,
    }


def test_conversation_title_is_normalized_and_limited():
    assert make_conversation_title("  Gợi ý   món sáng  ") == "Gợi ý món sáng"
    assert len(make_conversation_title("x" * 100)) == 80
    assert make_conversation_title("x" * 100).endswith("...")


def test_recent_history_keeps_five_latest_complete_turns_in_order():
    history = _recent_chat_history([_turn(number) for number in range(1, 8)])

    assert len(history) == 10
    assert history[0]["content"] == "user-3"
    assert history[-1]["content"] == "assistant-7"


def test_recent_history_respects_character_budget():
    turns = [_turn(1), _turn(2)]
    turns[0]["user_content"] = "old"
    turns[0]["assistant_content"] = "old"
    turns[1]["user_content"] = "x" * 7000
    turns[1]["assistant_content"] = "y" * 6000

    assert _recent_chat_history(turns) == []


class _Client:
    def __init__(self, replies: list[str] | None = None, *, unavailable=False):
        self.replies = list(replies or ["answer"])
        self.unavailable = unavailable
        self.messages = None

    def complete_text(self, messages):
        self.messages = messages
        if self.unavailable:
            raise AIUnavailableError("offline")
        return self.replies.pop(0)

    def stream_text(self, messages):
        self.messages = messages
        if self.unavailable:
            raise AIUnavailableError("offline")
        yield self.replies.pop(0)

    def complete_json(self, *args, **kwargs):
        raise NotImplementedError


class _MemoryStore:
    def __init__(self):
        now = datetime.now(timezone.utc)
        self.turn = {
            "id": 3,
            "turn_number": 2,
            "user_content": "Câu gần nhất",
            "assistant_content": "Câu trả lời cũ",
            "status": "completed",
            "created_at": now,
            "updated_at": now,
        }
        self.history = [_turn(1)]
        self.fail_kwargs = None

    def start_turn(self, *, user_id, message, conversation_id):
        self.turn = {**self.turn, "user_content": message, "assistant_content": None, "status": "pending"}
        return conversation_id or 7, self.turn

    def prepare_retry(self, *, conversation_id, turn_id, user_id):
        return dict(self.turn)

    def completed_turns_before(self, *, conversation_id, turn_number):
        return self.history

    def complete_turn(self, *, conversation_id, turn_id, assistant_content):
        self.turn = {**self.turn, "assistant_content": assistant_content, "status": "completed"}
        return self.turn

    def fail_turn(self, **kwargs):
        self.fail_kwargs = kwargs
        self.turn = {**self.turn, "status": "failed"}


def test_chat_uses_server_history_instead_of_client_history():
    store = _MemoryStore()
    client = _Client(["Mới"])
    events = list(ChatUseCase(client, store).open_chat_stream(
        ChatRequest(
            message="Câu mới",
            conversation_id=7,
            history=[{"role": "user", "content": "history giả từ client"}],
        ),
        user_id=1,
    ).events())

    assert events[-1]["data"]["reply"] == "Mới"
    assert client.messages[1]["content"] == "user-1"
    assert all(message["content"] != "history giả từ client" for message in client.messages)


def test_empty_chat_stream_marks_turn_failed():
    store = _MemoryStore()
    client = _Client(["   "])

    events = list(ChatUseCase(client, store).open_chat_stream(
        ChatRequest(message="Gợi ý món ăn", conversation_id=7),
        user_id=1,
    ).events())

    assert events[-1]["event"] == "error"
    assert store.fail_kwargs["turn_id"] == 3
    assert store.fail_kwargs["conversation_id"] == 7


def test_retry_replaces_latest_answer_without_creating_turn():
    store = _MemoryStore()
    client = _Client(["Câu trả lời mới"])

    events = list(ChatUseCase(client, store).open_retry_stream(
        conversation_id=7, turn_id=3, user_id=1
    ).events())

    assert events[-1]["data"]["turn"]["id"] == 3
    assert events[-1]["data"]["turn"]["assistant_content"] == "Câu trả lời mới"
    assert client.messages[-1] == {"role": "user", "content": "Câu gần nhất"}


def test_failed_retry_keeps_existing_answer():
    store = _MemoryStore()
    client = _Client(unavailable=True)

    events = list(ChatUseCase(client, store).open_retry_stream(
        conversation_id=7, turn_id=3, user_id=1
    ).events())

    assert events[-1]["event"] == "error"
    assert store.turn["assistant_content"] == "Câu trả lời cũ"
    assert store.turn["status"] == "failed"


def test_conversation_store_limits_and_ownership(db_session):
    first_email = f"ai-history-{uuid4()}@example.com"
    second_email = f"ai-history-{uuid4()}@example.com"
    first_user = int(
        db_session.execute(
            text(
                """INSERT INTO users (email, hashed_password, role)
                   VALUES (:email, 'test', 'user') RETURNING id"""
            ),
            {"email": first_email},
        ).scalar_one()
    )
    second_user = int(
        db_session.execute(
            text(
                """INSERT INTO users (email, hashed_password, role)
                   VALUES (:email, 'test', 'user') RETURNING id"""
            ),
            {"email": second_email},
        ).scalar_one()
    )
    db_session.commit()
    store = ConversationStore(db_session)

    try:
        first_conversation = None
        for index in range(10):
            conversation_id, turn = store.start_turn(
                user_id=first_user,
                message=f"Câu hỏi {index}",
                conversation_id=None,
            )
            store.complete_turn(
                conversation_id=conversation_id,
                turn_id=int(turn["id"]),
                assistant_content="Trả lời",
            )
            first_conversation = first_conversation or conversation_id

        summaries = store.list_for_user(first_user)
        assert len(summaries) == 10
        assert len(summaries[0]["last_message_preview"]) <= 160
        with pytest.raises(ConflictError, match="đủ 10"):
            store.start_turn(user_id=first_user, message="Câu thứ 11", conversation_id=None)
        with pytest.raises(NotFoundError):
            store.get_for_user(int(first_conversation), second_user)

        detail = store.get_for_user(int(first_conversation), first_user)
        assert detail["turn_count"] == 1
        store.delete_for_user(int(first_conversation), first_user)
        assert len(store.list_for_user(first_user)) == 9
    finally:
        db_session.execute(
            text("DELETE FROM users WHERE id IN (:first_user, :second_user)"),
            {"first_user": first_user, "second_user": second_user},
        )
        db_session.commit()


def test_conversation_store_limits_twenty_turns(db_session):
    email = f"ai-turns-{uuid4()}@example.com"
    user_id = int(
        db_session.execute(
            text(
                """INSERT INTO users (email, hashed_password, role)
                   VALUES (:email, 'test', 'user') RETURNING id"""
            ),
            {"email": email},
        ).scalar_one()
    )
    db_session.commit()
    store = ConversationStore(db_session)

    try:
        conversation_id = None
        for index in range(20):
            conversation_id, turn = store.start_turn(
                user_id=user_id,
                message=f"Câu hỏi {index + 1}",
                conversation_id=conversation_id,
            )
            store.complete_turn(
                conversation_id=conversation_id,
                turn_id=int(turn["id"]),
                assistant_content="Trả lời",
            )
        with pytest.raises(ConflictError, match="20 câu"):
            store.start_turn(
                user_id=user_id,
                message="Câu 21",
                conversation_id=conversation_id,
            )
    finally:
        db_session.execute(text("DELETE FROM users WHERE id=:id"), {"id": user_id})
        db_session.commit()

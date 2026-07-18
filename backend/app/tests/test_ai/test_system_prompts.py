from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from app.core.deps import require_super_admin
from app.modules.ai.admin_router import router as admin_ai_router
from app.modules.ai.prompt_store import SystemPromptStore
from app.modules.ai.prompts import DEFAULT_SYSTEM_PROMPTS, PROMPT_FEATURES
from app.modules.identity.domain import UserEntity
from app.shared.enums import UserRole


class _Rows:
    def __init__(self, *, rows=None, row=None) -> None:
        self._rows = rows or []
        self._row = row

    def mappings(self):
        return self

    def all(self):
        return self._rows

    def first(self):
        return self._row


class _PromptSession:
    def __init__(self) -> None:
        self.overrides: dict[str, dict] = {}
        self.audits: list[dict] = []
        self.commits = 0

    def execute(self, statement, params=None):
        sql = " ".join(str(statement).split())
        params = params or {}
        if sql.startswith("SELECT feature, content, updated_at FROM ai_system_prompts WHERE"):
            return _Rows(row=self.overrides.get(params["feature"]))
        if sql.startswith("SELECT feature, content, updated_at FROM ai_system_prompts"):
            return _Rows(rows=list(self.overrides.values()))
        if sql.startswith("SELECT content FROM ai_system_prompts"):
            return _Rows(row=self.overrides.get(params["feature"]))
        if sql.startswith("INSERT INTO ai_system_prompts"):
            self.overrides[params["feature"]] = {
                "feature": params["feature"],
                "content": params["content"],
                "updated_at": datetime.now(timezone.utc),
            }
            return _Rows()
        if sql.startswith("DELETE FROM ai_system_prompts"):
            self.overrides.pop(params["feature"], None)
            return _Rows()
        if sql.startswith("INSERT INTO audit_logs"):
            self.audits.append(params)
            return _Rows()
        raise AssertionError(f"Unexpected SQL: {sql}")

    def commit(self):
        self.commits += 1


def test_system_prompt_store_lists_defaults_in_stable_feature_order():
    store = SystemPromptStore(_PromptSession())

    items = store.list()

    assert [item["feature"] for item in items] == list(PROMPT_FEATURES)
    assert all(item["is_custom"] is False for item in items)
    assert items[0]["content"] == DEFAULT_SYSTEM_PROMPTS["chat"]


def test_system_prompt_store_updates_resolves_and_resets_override():
    session = _PromptSession()
    store = SystemPromptStore(session)

    updated = store.update("chat", "Prompt quản trị tùy chỉnh", actor_id=7)

    assert updated["is_custom"] is True
    assert store.get_effective("chat") == "Prompt quản trị tùy chỉnh"
    assert session.audits[-1]["action"] == "update"

    reset = store.reset("chat", actor_id=7)

    assert reset == {
        "feature": "chat",
        "content": DEFAULT_SYSTEM_PROMPTS["chat"],
        "is_custom": False,
        "updated_at": None,
    }
    assert store.get_effective("chat") == DEFAULT_SYSTEM_PROMPTS["chat"]
    assert session.audits[-1]["action"] == "reset"
    assert session.commits == 2


def test_resetting_default_prompt_is_idempotent_without_audit():
    session = _PromptSession()

    result = SystemPromptStore(session).reset("suggest_swap", actor_id=7)

    assert result["content"] == DEFAULT_SYSTEM_PROMPTS["suggest_swap"]
    assert session.audits == []
    assert session.commits == 0


def test_system_prompt_routes_use_super_admin_gate():
    prompt_routes = [
        route for route in admin_ai_router.routes
        if getattr(route, "path", "").startswith("/api/admin/ai/prompts")
    ]

    assert len(prompt_routes) == 3
    for route in prompt_routes:
        dependency_calls = {dependency.call for dependency in route.dependant.dependencies}
        assert require_super_admin in dependency_calls


def test_super_admin_gate_rejects_data_editor_and_keeps_legacy_admin_compatible():
    data_editor = UserEntity(
        id=2, email="editor@example.com", hashed_password="hash", role=UserRole.DATA_EDITOR,
    )
    legacy_admin = UserEntity(
        id=1, email="admin@example.com", hashed_password="hash", role=UserRole.ADMIN,
    )

    with pytest.raises(HTTPException) as exc_info:
        require_super_admin(data_editor)

    assert exc_info.value.status_code == 403
    assert require_super_admin(legacy_admin) is legacy_admin

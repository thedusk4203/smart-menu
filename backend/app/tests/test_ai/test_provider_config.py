from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from app.core.config import settings
from app.modules.ai.client import OpenAICompatibleAIClient
from app.modules.ai.exceptions import AIResponseValidationError
from app.modules.ai.provider_store import decrypt_secret, encrypt_secret, validate_base_url
from app.modules.ai.schemas import ChatRequest
from app.modules.ai.admin_schemas import ProviderWrite, SystemPromptWrite


def test_api_key_round_trip_and_mask(monkeypatch):
    monkeypatch.setattr(settings, "ai_config_encryption_key", "test-master-key")
    encrypted, suffix = encrypt_secret("sk-secret-1234")

    assert encrypted != "sk-secret-1234"
    assert suffix == "1234"
    assert decrypt_secret(encrypted) == "sk-secret-1234"


def test_base_url_blocks_metadata_endpoint():
    with pytest.raises(Exception, match="metadata"):
        validate_base_url("http://169.254.169.254/latest")


def test_google_provider_is_supported():
    provider = ProviderWrite(
        name="Gemini", provider_type="google",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai",
        model="gemini-test", api_key="secret",
    )
    assert provider.provider_type == "google"


def test_system_prompt_content_is_trimmed_and_bounded():
    assert SystemPromptWrite(content="  Prompt mới  ").content == "Prompt mới"

    with pytest.raises(ValidationError):
        SystemPromptWrite(content="   ")
    with pytest.raises(ValidationError):
        SystemPromptWrite(content="x" * 20_001)


def test_chat_history_total_is_limited():
    with pytest.raises(ValidationError, match="12000"):
        ChatRequest(message="hi", history=[
            {"role": "user", "content": "x" * 4000},
            {"role": "assistant", "content": "x" * 4000},
            {"role": "user", "content": "x" * 4000},
            {"role": "assistant", "content": "x"},
        ])


def test_empty_ai_message_is_rejected():
    with pytest.raises(AIResponseValidationError, match="không trả về nội dung"):
        OpenAICompatibleAIClient._extract_message_content(
            {"choices": [{"message": {"content": "  \n "}}]}
        )


class _CapturingClient(OpenAICompatibleAIClient):
    def __init__(self, mode: str):
        super().__init__(base_url="http://localhost:1234/v1", model="test",
                         structured_output_mode=mode)
        self.payload = None

    def _request_json(self, method, path, payload=None):
        self.payload = payload
        return {"choices": [{"message": {"content": '{"ok": true}'}}], "usage": {}}


@pytest.mark.parametrize("mode,expected", [("json_schema", "json_schema"), ("json_object", "json_object")])
def test_structured_output_mode(mode, expected):
    client = _CapturingClient(mode)
    assert client.complete_json(
        [{"role": "user", "content": "json"}], schema_name="health",
        json_schema={"type": "object"},
    ) == {"ok": True}
    assert client.payload["response_format"]["type"] == expected
    assert client.payload["stream"] is False
    assert "temperature" not in client.payload
    assert "max_tokens" not in client.payload


class _StreamingResponse:
    def __init__(self, lines: list[bytes]) -> None:
        self.lines = lines

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def __iter__(self):
        return iter(self.lines)


def test_chat_stream_uses_model_defaults_and_yields_content(monkeypatch):
    captured: dict = {}

    def fake_urlopen(request, timeout):
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        assert timeout == 60
        return _StreamingResponse([
            b'data: {"choices":[{"delta":{"role":"assistant"}}]}\n',
            b'data: {"choices":[{"delta":{"content":"Xin "}}]}\n',
            b'data: {"choices":[{"delta":{"content":"chao"},"finish_reason":"stop"}]}\n',
            b'data: [DONE]\n',
        ])

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    client = OpenAICompatibleAIClient(base_url="http://localhost:1234/v1", model="test")

    assert "".join(client.stream_text([{"role": "user", "content": "Hi"}])) == "Xin chao"
    assert captured["payload"]["stream"] is True
    assert "temperature" not in captured["payload"]
    assert "max_tokens" not in captured["payload"]

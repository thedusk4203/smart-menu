# File: backend/app/modules/ai/client.py
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from app.modules.ai.exceptions import AIResponseValidationError, AIUnavailableError
from app.modules.ai.ports import AIClientPort, AIMessage


class DisabledAIClient(AIClientPort):
    def complete_text(
        self,
        messages: list[AIMessage],
        *,
        temperature: float = 0.4,
        max_tokens: int = 700,
    ) -> str:
        raise AIUnavailableError("AI chưa được bật. Hãy cấu hình AI_PROVIDER và AI_MODEL.")

    def complete_json(
        self,
        messages: list[AIMessage],
        *,
        schema_name: str,
        json_schema: dict[str, Any],
        temperature: float = 0.1,
        max_tokens: int = 700,
    ) -> dict[str, Any]:
        raise AIUnavailableError("AI chưa được bật. Hãy cấu hình AI_PROVIDER và AI_MODEL.")


class OpenAICompatibleAIClient(AIClientPort):
    """Client dùng endpoint OpenAI-compatible, bao gồm LM Studio local server."""

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        api_key: str | None = None,
        timeout_seconds: float = 60,
    ) -> None:
        if not base_url:
            raise AIUnavailableError("Thiếu AI_BASE_URL cho AI provider.")
        self._base_url = base_url.rstrip("/")
        self._model = model.strip()
        self._api_key = api_key
        self._timeout_seconds = timeout_seconds

    def complete_text(
        self,
        messages: list[AIMessage],
        *,
        temperature: float = 0.4,
        max_tokens: int = 700,
    ) -> str:
        data = self._create_chat_completion(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return self._extract_message_content(data)

    def complete_json(
        self,
        messages: list[AIMessage],
        *,
        schema_name: str,
        json_schema: dict[str, Any],
        temperature: float = 0.1,
        max_tokens: int = 700,
    ) -> dict[str, Any]:
        data = self._create_chat_completion(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": schema_name,
                    "strict": True,
                    "schema": json_schema,
                },
            },
        )
        content = self._extract_message_content(data)
        try:
            parsed = json.loads(self._strip_json_fence(content))
        except json.JSONDecodeError as exc:
            raise AIResponseValidationError("AI trả về JSON không hợp lệ.") from exc
        if not isinstance(parsed, dict):
            raise AIResponseValidationError("AI phải trả về một JSON object.")
        return parsed

    def _create_chat_completion(
        self,
        messages: list[AIMessage],
        *,
        temperature: float,
        max_tokens: int,
        response_format: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self._resolve_model(),
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        if response_format is not None:
            payload["response_format"] = response_format
        return self._request_json("POST", "chat/completions", payload)

    def _resolve_model(self) -> str:
        if self._model:
            return self._model

        data = self._request_json("GET", "models")
        models = data.get("data")
        if not isinstance(models, list) or not models:
            raise AIUnavailableError(
                "Không tìm thấy model nào từ AI provider. Hãy load model trong LM Studio hoặc set AI_MODEL."
            )
        first = models[0]
        if not isinstance(first, dict) or not first.get("id"):
            raise AIUnavailableError("Response /models không có model id hợp lệ.")
        self._model = str(first["id"])
        return self._model

    def _request_json(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self._base_url}/{path.lstrip('/')}"
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = urllib.request.Request(
            url,
            data=body,
            headers=self._headers(),
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=self._timeout_seconds) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")[:500]
            raise AIUnavailableError(
                f"AI provider trả lỗi HTTP {exc.code}: {detail or exc.reason}"
            ) from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise AIUnavailableError(f"Không kết nối được AI provider: {exc}") from exc

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise AIUnavailableError("AI provider trả về response không phải JSON.") from exc
        if not isinstance(data, dict):
            raise AIUnavailableError("AI provider trả về JSON không đúng định dạng.")
        return data

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    @staticmethod
    def _extract_message_content(data: dict[str, Any]) -> str:
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise AIUnavailableError("AI provider trả về response thiếu choices[0].message.content.") from exc

        if isinstance(content, str):
            return content.strip()
        raise AIUnavailableError("AI provider trả về message content không phải chuỗi.")

    @staticmethod
    def _strip_json_fence(content: str) -> str:
        text = content.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()
        return text

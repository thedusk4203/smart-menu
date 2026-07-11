# File: backend/app/modules/ai/client.py
from __future__ import annotations

import json
import urllib.error
import urllib.request
from collections.abc import Callable, Iterator
from time import perf_counter
from typing import Any

from app.modules.ai.exceptions import AIResponseValidationError, AIUnavailableError
from app.modules.ai.ports import AIClientPort, AIMessage
from app.modules.ai.provider_store import AIRequestLogStore, ProviderConfig


class DisabledAIClient(AIClientPort):
    def complete_text(
        self,
        messages: list[AIMessage],
    ) -> str:
        raise AIUnavailableError("AI chưa được bật. Hãy cấu hình AI_PROVIDER và AI_MODEL.")

    def stream_text(self, messages: list[AIMessage]) -> Iterator[str]:
        raise AIUnavailableError("AI chưa được bật. Hãy cấu hình AI_PROVIDER và AI_MODEL.")

    def complete_json(
        self,
        messages: list[AIMessage],
        *,
        schema_name: str,
        json_schema: dict[str, Any],
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
        structured_output_mode: str = "json_schema",
    ) -> None:
        if not base_url:
            raise AIUnavailableError("Thiếu AI_BASE_URL cho AI provider.")
        self._base_url = base_url.rstrip("/")
        self._model = model.strip()
        self._api_key = api_key
        self._timeout_seconds = timeout_seconds
        self._structured_output_mode = structured_output_mode
        self.last_usage: dict[str, int | None] = {}

    def complete_text(
        self,
        messages: list[AIMessage],
    ) -> str:
        data = self._create_chat_completion(messages)
        return self._extract_message_content(data)

    def stream_text(self, messages: list[AIMessage]) -> Iterator[str]:
        """Trả từng content delta từ OpenAI-compatible SSE stream."""
        payload = {
            "model": self._resolve_model(),
            "messages": messages,
            "stream": True,
        }
        url = f"{self._base_url}/chat/completions"
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={**self._headers(), "Accept": "text/event-stream"},
            method="POST",
        )
        saw_terminal = False
        saw_content = False
        try:
            with urllib.request.urlopen(request, timeout=self._timeout_seconds) as response:
                for raw_line in response:
                    line = raw_line.decode("utf-8").strip()
                    if not line or line.startswith(":") or line.startswith("event:"):
                        continue
                    if not line.startswith("data:"):
                        continue
                    raw_data = line[5:].strip()
                    if raw_data == "[DONE]":
                        saw_terminal = True
                        break
                    try:
                        data = json.loads(raw_data)
                    except json.JSONDecodeError as exc:
                        raise AIUnavailableError("AI provider trả về SSE không hợp lệ.") from exc
                    if not isinstance(data, dict):
                        raise AIUnavailableError("AI provider trả về SSE không đúng định dạng.")
                    self._update_usage(data)
                    if isinstance(data.get("error"), dict):
                        detail = data["error"].get("message")
                        raise AIUnavailableError(
                            f"AI provider trả lỗi: {detail or 'không xác định'}"
                        )
                    choices = data.get("choices")
                    if not isinstance(choices, list) or not choices:
                        continue
                    choice = choices[0]
                    if not isinstance(choice, dict):
                        continue
                    delta = choice.get("delta")
                    content = delta.get("content") if isinstance(delta, dict) else None
                    if isinstance(content, str) and content:
                        saw_content = True
                        yield content
                    if choice.get("finish_reason") is not None:
                        saw_terminal = True
                if not saw_terminal:
                    raise AIUnavailableError("AI provider đóng stream trước khi hoàn tất.")
                if not saw_content:
                    raise AIResponseValidationError("AI provider không trả về nội dung trả lời.")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")[:500]
            raise AIUnavailableError(
                f"AI provider trả lỗi HTTP {exc.code}: {detail or exc.reason}"
            ) from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise AIUnavailableError(f"Không kết nối được AI provider: {exc}") from exc

    def complete_json(
        self,
        messages: list[AIMessage],
        *,
        schema_name: str,
        json_schema: dict[str, Any],
    ) -> dict[str, Any]:
        response_format: dict[str, Any]
        effective_messages = messages
        if self._structured_output_mode == "json_object":
            response_format = {"type": "json_object"}
            effective_messages = [
                *messages,
                {"role": "user", "content": "Trả về JSON khớp chính xác schema sau: " + json.dumps(json_schema, ensure_ascii=False)},
            ]
        else:
            response_format = {
                "type": "json_schema",
                "json_schema": {"name": schema_name, "strict": True, "schema": json_schema},
            }
        data = self._create_chat_completion(
            effective_messages,
            response_format=response_format,
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
        response_format: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self._resolve_model(),
            "messages": messages,
            "stream": False,
        }
        if response_format is not None:
            payload["response_format"] = response_format
        data = self._request_json("POST", "chat/completions", payload)
        self._update_usage(data)
        return data

    def list_models(self) -> list[str]:
        data = self._request_json("GET", "models")
        models = data.get("data")
        if not isinstance(models, list):
            return []
        return [str(item["id"]) for item in models if isinstance(item, dict) and item.get("id")]

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

    def _update_usage(self, data: dict[str, Any]) -> None:
        usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
        self.last_usage = {
            "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
            "total_tokens": usage.get("total_tokens"),
        }

    @staticmethod
    def _extract_message_content(data: dict[str, Any]) -> str:
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise AIUnavailableError("AI provider trả về response thiếu choices[0].message.content.") from exc

        if isinstance(content, str):
            normalized = content.strip()
            if not normalized:
                raise AIResponseValidationError("AI provider không trả về nội dung trả lời.")
            return normalized
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


class LoggedAIClient(AIClientPort):
    """Ghi đúng payload gửi LLM và response, nhưng không bao giờ ghi headers/API key."""

    def __init__(self, inner: AIClientPort, store: AIRequestLogStore, config: ProviderConfig,
                 *, user_id: int, feature: str) -> None:
        self.inner = inner
        self.store = store
        self.config = config
        self.user_id = user_id
        self.feature = feature

    def complete_text(self, messages: list[AIMessage]) -> str:
        return self._run(messages, {"stream": False}, lambda: self.inner.complete_text(messages))

    def stream_text(self, messages: list[AIMessage]) -> Iterator[str]:
        return self._run_stream(messages, {"stream": True}, lambda: self.inner.stream_text(messages))

    def complete_json(self, messages: list[AIMessage], *, schema_name: str,
                      json_schema: dict[str, Any]) -> dict[str, Any]:
        return self._run(
            messages,
            {"stream": False, "schema_name": schema_name, "json_schema": json_schema},
            lambda: self.inner.complete_json(messages, schema_name=schema_name,
                                             json_schema=json_schema),
        )

    def _run_stream(
        self,
        messages: list[AIMessage],
        options: dict[str, Any],
        call: Callable[[], Iterator[str]],
    ) -> Iterator[str]:
        started = perf_counter()
        request_data = {"messages": messages, **options}
        chunks: list[str] = []
        stream = call()
        logged = False
        try:
            for chunk in stream:
                chunks.append(chunk)
                yield chunk
        except GeneratorExit:
            self._write(request_data, None, "error", started, "AI stream bị ngắt trước khi hoàn tất.")
            logged = True
            raise
        except Exception as exc:
            self._write(request_data, None, "error", started, str(exc)[:1000])
            logged = True
            raise
        else:
            self._write(request_data, "".join(chunks), "success", started, None)
            logged = True
        finally:
            close = getattr(stream, "close", None)
            if callable(close):
                close()
            if not logged:
                self._write(request_data, None, "error", started, "AI stream bị ngắt trước khi hoàn tất.")

    def _run(self, messages: list[AIMessage], options: dict[str, Any], call):
        started = perf_counter()
        request_data = {"messages": messages, **options}
        try:
            result = call()
        except Exception as exc:
            self._write(request_data, None, "error", started, str(exc)[:1000])
            raise
        self._write(request_data, result, "success", started, None)
        return result

    def _write(self, request_data: dict[str, Any], response: Any, status: str,
               started: float, error: str | None) -> None:
        usage = getattr(self.inner, "last_usage", {})
        self.store.write(
            user_id=self.user_id,
            provider_config_id=self.config.id,
            feature=self.feature,
            provider_type=self.config.provider_type,
            model=self.config.model,
            request_data=request_data,
            response_data={"content": response} if response is not None else None,
            status=status,
            latency_ms=round((perf_counter() - started) * 1000),
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
            total_tokens=usage.get("total_tokens"),
            error_message=error,
        )

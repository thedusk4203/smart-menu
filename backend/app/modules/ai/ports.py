# File: backend/app/modules/ai/ports.py
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import Any, Literal, TypedDict


class AIMessage(TypedDict):
    role: Literal["system", "user", "assistant"]
    content: str


class AIClientPort(ABC):
    @abstractmethod
    def complete_text(
        self,
        messages: list[AIMessage],
    ) -> str: ...

    @abstractmethod
    def stream_text(self, messages: list[AIMessage]) -> Iterator[str]: ...

    @abstractmethod
    def complete_json(
        self,
        messages: list[AIMessage],
        *,
        schema_name: str,
        json_schema: dict[str, Any],
    ) -> dict[str, Any]: ...

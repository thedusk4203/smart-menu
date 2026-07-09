# File: backend/app/modules/ai/ports.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Literal, TypedDict


class AIMessage(TypedDict):
    role: Literal["system", "user", "assistant"]
    content: str


class AIClientPort(ABC):
    @abstractmethod
    def complete_text(
        self,
        messages: list[AIMessage],
        *,
        temperature: float = 0.4,
        max_tokens: int = 700,
    ) -> str: ...

    @abstractmethod
    def complete_json(
        self,
        messages: list[AIMessage],
        *,
        schema_name: str,
        json_schema: dict[str, Any],
        temperature: float = 0.1,
        max_tokens: int = 700,
    ) -> dict[str, Any]: ...

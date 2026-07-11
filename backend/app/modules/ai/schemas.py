# File: backend/app/modules/ai/schemas.py
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    context: Any | None = None

    @field_validator("message")
    @classmethod
    def strip_message(cls, value: str) -> str:
        return value.strip()


class ChatResponse(BaseModel):
    reply: str


class ParseMenuRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)

    @field_validator("message")
    @classmethod
    def strip_message(cls, value: str) -> str:
        return value.strip()


class ParsedMenuRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    days: int | None = Field(default=None, ge=1, le=14)
    meals_per_day: int | None = Field(default=None, ge=2, le=3)
    budget_limit: float | None = Field(default=None, ge=0)
    preferred_tags: list[str] = Field(default_factory=list)
    needs_clarification: bool = False
    clarification_question: str | None = None


class ExplainPlanRequest(BaseModel):
    plan_data: dict[str, Any]
    total_cost: float | None = None
    total_calories: float | None = None
    budget_limit: float | None = None


class SwapSuggestionRequest(BaseModel):
    meal_id: int
    meal_type: str
    note: str | None = None


class SwapSuggestion(BaseModel):
    meal_id: int
    name: str
    reason: str | None = None

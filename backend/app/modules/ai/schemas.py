from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    conversation_id: int | None = Field(default=None, gt=0)
    context: Any | None = None
    # Giữ tạm field cũ để client phiên bản trước không lỗi validation. Backend
    # không còn tin history do client gửi; lịch sử chính thức được đọc từ DB.
    history: list[ChatMessage] = Field(default_factory=list, max_length=10)

    @field_validator("message")
    @classmethod
    def strip_message(cls, value: str) -> str:
        return value.strip()

    @model_validator(mode="after")
    def limit_history(self) -> "ChatRequest":
        if sum(len(item.content) for item in self.history) > 12000:
            raise ValueError("Tổng lịch sử hội thoại không được vượt quá 12000 ký tự")
        return self


class ChatResponse(BaseModel):
    reply: str


class ConversationTurn(BaseModel):
    id: int
    turn_number: int = Field(ge=1, le=20)
    user_content: str
    assistant_content: str | None = None
    status: Literal["pending", "completed", "failed"]
    created_at: datetime
    updated_at: datetime


class ConversationChatResponse(ChatResponse):
    conversation_id: int
    turn: ConversationTurn


class ConversationSummary(BaseModel):
    id: int
    title: str
    turn_count: int = Field(ge=0, le=20)
    last_message_preview: str | None = None
    created_at: datetime
    updated_at: datetime


class ConversationDetail(ConversationSummary):
    turns: list[ConversationTurn]


class ParseMenuRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)

    @field_validator("message")
    @classmethod
    def strip_message(cls, value: str) -> str:
        return value.strip()


class ParsedMenuRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    days: int | None = Field(default=None, ge=1, le=7)
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


class PlanExplanationContent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str = Field(min_length=20, max_length=500)
    budget_assessment: str = Field(min_length=10, max_length=400)
    nutrition_assessment: str = Field(min_length=10, max_length=400)
    highlights: list[str] = Field(min_length=1, max_length=3)
    cautions: list[str] = Field(default_factory=list, max_length=3)
    recommendations: list[str] = Field(min_length=1, max_length=3)

    @field_validator("summary", "budget_assessment", "nutrition_assessment")
    @classmethod
    def normalize_explanation_text(cls, value: str) -> str:
        return " ".join(value.split())

    @field_validator("highlights", "cautions", "recommendations")
    @classmethod
    def normalize_explanation_items(cls, value: list[str]) -> list[str]:
        normalized = [" ".join(item.split()) for item in value if item.strip()]
        if len(normalized) != len(value):
            raise ValueError("các ý phân tích không được để trống")
        return normalized


class ExplainPlanResponse(PlanExplanationContent):
    # Giữ reply để client cũ vẫn hiển thị được bản phân tích dạng văn bản.
    reply: str


class SwapSuggestionRequest(BaseModel):
    day: int = Field(ge=1, le=7)
    meal_type: Literal["breakfast", "lunch", "dinner"]
    target_dish_id: int = Field(gt=0)
    plan: dict[str, Any]
    note: str | None = Field(default=None, max_length=1000)


class SwapSuggestion(BaseModel):
    dish_id: int
    name: str
    reason: str | None = None
    plan: dict[str, Any]

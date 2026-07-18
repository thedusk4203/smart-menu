from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

ProviderType = Literal["openai", "deepseek", "lmstudio", "google", "custom"]


class ProviderWrite(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    provider_type: ProviderType
    base_url: str = Field(min_length=1, max_length=500)
    model: str = Field(min_length=1, max_length=200)
    api_key: str | None = Field(default=None, max_length=1000)
    clear_api_key: bool = False
    timeout_seconds: float = Field(default=60, ge=1, le=300)

    @field_validator("name", "base_url", "model")
    @classmethod
    def strip_required(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("không được để trống")
        return value


class ProviderItem(BaseModel):
    id: int
    name: str
    provider_type: ProviderType
    base_url: str
    model: str
    has_api_key: bool
    masked_api_key: str | None = None
    timeout_seconds: float
    structured_output_mode: str | None = None
    config_version: int
    tested_version: int | None = None
    test_status: str
    last_tested_at: datetime | None = None
    last_test_error: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ProviderTestResult(BaseModel):
    provider: ProviderItem
    models: list[str] = Field(default_factory=list)


PromptFeature = Literal["chat", "parse_menu", "explain_plan", "suggest_swap"]


class SystemPromptWrite(BaseModel):
    content: str = Field(min_length=1, max_length=20_000)

    @field_validator("content")
    @classmethod
    def strip_content(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("không được để trống")
        return value


class SystemPromptItem(BaseModel):
    feature: PromptFeature
    content: str
    is_custom: bool
    updated_at: datetime | None = None


class AIStatus(BaseModel):
    enabled: bool
    source: str | None = None
    provider_name: str | None = None
    provider_type: str | None = None
    model: str | None = None
    features: list[str] = Field(default_factory=list)


class AILogItem(BaseModel):
    id: int
    user_id: int | None
    provider_config_id: int | None
    feature: str
    provider_type: str
    model: str
    status: str
    latency_ms: int
    prompt_tokens: int | None
    completion_tokens: int | None
    total_tokens: int | None
    error_message: str | None
    created_at: datetime
    expires_at: datetime


class AILogDetail(AILogItem):
    request_data: dict[str, Any]
    response_data: Any | None


class AILogPage(BaseModel):
    items: list[AILogItem]
    total: int
    limit: int
    offset: int


class PurgeLogsRequest(BaseModel):
    before: datetime


class PurgeLogsResponse(BaseModel):
    deleted: int

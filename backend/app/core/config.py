# File: backend/app/core/config.py
# Application configuration, loaded from environment variables (.env).
from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _default_ai_base_url(provider: str) -> str:
    if provider == "lmstudio":
        return "http://localhost:1234/v1"
    if provider == "deepseek":
        return "https://api.deepseek.com/v1"
    if provider == "openai":
        return "https://api.openai.com/v1"
    if provider == "google":
        return "https://generativelanguage.googleapis.com/v1beta/openai"
    return ""


class Settings:
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:postgres@localhost:5432/DATN",
    )
    secret_key: str = os.getenv("SECRET_KEY", "change-me-in-env")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    ai_provider: str = os.getenv("AI_PROVIDER", "disabled").strip().lower()
    ai_enabled: bool = _env_bool("AI_ENABLED", ai_provider not in {"", "disabled", "none", "off"})
    ai_base_url: str = os.getenv("AI_BASE_URL", _default_ai_base_url(ai_provider)).rstrip("/")
    ai_api_key: str | None = os.getenv(
        "AI_API_KEY",
        "lm-studio" if ai_provider == "lmstudio" else None,
    )
    ai_model: str = os.getenv("AI_MODEL", "").strip()
    ai_timeout_seconds: float = float(os.getenv("AI_TIMEOUT_SECONDS", "60"))
    ai_config_encryption_key: str | None = os.getenv("AI_CONFIG_ENCRYPTION_KEY")


settings = Settings()

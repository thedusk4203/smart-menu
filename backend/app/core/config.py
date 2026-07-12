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


def _env_list(name: str, default: str) -> list[str]:
    return [value.strip() for value in os.getenv(name, default).split(",") if value.strip()]


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
    app_env: str = os.getenv("APP_ENV", "development").strip().lower()
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
    cors_origins: list[str] = _env_list(
        "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    )

    def validate_runtime(self) -> None:
        if self.app_env in {"development", "test"}:
            return
        invalid_values = {"", "change-me-in-env", "change-this-to-a-long-random-secret"}
        if self.secret_key in invalid_values:
            raise RuntimeError("SECRET_KEY phải được cấu hình ngoài môi trường development.")
        if not self.cors_origins:
            raise RuntimeError("CORS_ORIGINS phải có ít nhất một origin ngoài development.")
        if self.ai_enabled and (not self.ai_config_encryption_key or self.ai_config_encryption_key in invalid_values):
            raise RuntimeError("AI_CONFIG_ENCRYPTION_KEY phải được cấu hình khi AI được bật.")


settings = Settings()
settings.validate_runtime()

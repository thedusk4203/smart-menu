from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import text
from sqlmodel import Session

from app.core.config import settings
from app.core.exceptions import ConflictError, NotFoundError, ValidationAppError


PROVIDER_BASE_URLS = {
    "openai": "https://api.openai.com/v1",
    "deepseek": "https://api.deepseek.com/v1",
    "lmstudio": "http://localhost:1234/v1",
    "google": "https://generativelanguage.googleapis.com/v1beta/openai",
}


@dataclass(frozen=True)
class ProviderConfig:
    id: int | None
    name: str
    provider_type: str
    base_url: str
    model: str
    api_key: str | None
    timeout_seconds: float
    structured_output_mode: str | None = None
    source: str = "database"


def _fernet() -> Fernet:
    secret = settings.ai_config_encryption_key
    if not secret:
        raise ValidationAppError(
            "Server chưa cấu hình AI_CONFIG_ENCRYPTION_KEY nên không thể lưu API key."
        )
    key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode("utf-8")).digest())
    return Fernet(key)


def encrypt_secret(value: str | None) -> tuple[str | None, str | None]:
    if not value:
        return None, None
    return _fernet().encrypt(value.encode("utf-8")).decode("ascii"), value[-4:]


def decrypt_secret(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return _fernet().decrypt(value.encode("ascii")).decode("utf-8")
    except InvalidToken as exc:
        raise ValidationAppError(
            "Không giải mã được API key. Hãy kiểm tra AI_CONFIG_ENCRYPTION_KEY hoặc nhập lại key."
        ) from exc


def validate_base_url(value: str) -> str:
    normalized = value.strip().rstrip("/")
    parsed = urlparse(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username:
        raise ValidationAppError("Base URL phải là URL http/https hợp lệ và không chứa credentials.")
    if parsed.hostname in {"169.254.169.254", "metadata.google.internal"}:
        raise ValidationAppError("Không cho phép truy cập metadata endpoint nội bộ.")
    return normalized


class ProviderConfigStore:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list(self) -> list[dict[str, Any]]:
        rows = self.session.execute(
            text("""SELECT id, name, provider_type, base_url, model, api_key_suffix,
                           timeout_seconds, structured_output_mode, config_version,
                           tested_version, test_status, last_tested_at, last_test_error,
                           is_active, created_at, updated_at
                    FROM llm_provider_configs ORDER BY is_active DESC, updated_at DESC""")
        ).mappings().all()
        return [self._public(dict(row)) for row in rows]

    def get(self, config_id: int, *, include_secret: bool = False) -> dict[str, Any]:
        row = self.session.execute(
            text("SELECT * FROM llm_provider_configs WHERE id = :id"), {"id": config_id}
        ).mappings().first()
        if row is None:
            raise NotFoundError("Không tìm thấy cấu hình LLM provider.")
        result = dict(row)
        if include_secret:
            result["api_key"] = decrypt_secret(result.get("encrypted_api_key"))
        return result

    def active(self) -> ProviderConfig | None:
        self.session.execute(text("DELETE FROM ai_request_logs WHERE expires_at < NOW()"))
        self.session.commit()
        row = self.session.execute(
            text("SELECT * FROM llm_provider_configs WHERE is_active = TRUE LIMIT 1")
        ).mappings().first()
        if row is None:
            count = self.session.execute(text("SELECT COUNT(*) FROM llm_provider_configs")).scalar_one()
            if count == 0 and settings.ai_enabled:
                return ProviderConfig(
                    id=None,
                    name="Environment",
                    provider_type=settings.ai_provider,
                    base_url=settings.ai_base_url,
                    model=settings.ai_model,
                    api_key=settings.ai_api_key,
                    timeout_seconds=settings.ai_timeout_seconds,
                    structured_output_mode=(
                        "json_object" if settings.ai_provider == "deepseek" else "json_schema"
                    ),
                    source="environment",
                )
            return None
        data = dict(row)
        return ProviderConfig(
            id=int(data["id"]),
            name=str(data["name"]),
            provider_type=str(data["provider_type"]),
            base_url=str(data["base_url"]),
            model=str(data["model"]),
            api_key=decrypt_secret(data.get("encrypted_api_key")),
            timeout_seconds=float(data["timeout_seconds"]),
            structured_output_mode=data.get("structured_output_mode"),
        )

    def create(self, data: Any, actor_id: int) -> dict[str, Any]:
        encrypted, suffix = encrypt_secret(data.api_key)
        base_url = validate_base_url(data.base_url or PROVIDER_BASE_URLS.get(data.provider_type, ""))
        row = self.session.execute(
            text("""INSERT INTO llm_provider_configs
                    (name, provider_type, base_url, model, encrypted_api_key, api_key_suffix,
                     timeout_seconds, created_by, updated_by)
                    VALUES (:name, :ptype, :url, :model, :key, :suffix, :timeout, :actor, :actor)
                    RETURNING id"""),
            {"name": data.name.strip(), "ptype": data.provider_type, "url": base_url,
             "model": data.model.strip(), "key": encrypted, "suffix": suffix,
             "timeout": data.timeout_seconds, "actor": actor_id},
        ).scalar_one()
        self._audit(actor_id, "create", int(row), after={"name": data.name, "provider_type": data.provider_type})
        self.session.commit()
        return self._public(self.get(int(row)))

    def update(self, config_id: int, data: Any, actor_id: int) -> dict[str, Any]:
        current = self.get(config_id)
        if current["is_active"]:
            raise ConflictError("Không thể sửa provider đang active. Hãy clone thành draft trước.")
        encrypted = current.get("encrypted_api_key")
        suffix = current.get("api_key_suffix")
        if data.clear_api_key:
            encrypted, suffix = None, None
        elif data.api_key:
            encrypted, suffix = encrypt_secret(data.api_key)
        base_url = validate_base_url(data.base_url or PROVIDER_BASE_URLS.get(data.provider_type, ""))
        self.session.execute(
            text("""UPDATE llm_provider_configs SET
                    name=:name, provider_type=:ptype, base_url=:url, model=:model,
                    encrypted_api_key=:key, api_key_suffix=:suffix, timeout_seconds=:timeout,
                    config_version=config_version+1, tested_version=NULL, test_status='untested',
                    structured_output_mode=NULL, last_test_error=NULL,
                    updated_by=:actor, updated_at=NOW() WHERE id=:id"""),
            {"id": config_id, "name": data.name.strip(), "ptype": data.provider_type,
             "url": base_url, "model": data.model.strip(), "key": encrypted,
             "suffix": suffix, "timeout": data.timeout_seconds, "actor": actor_id},
        )
        self._audit(actor_id, "update", config_id, before=self._safe_audit(current),
                    after={"name": data.name, "provider_type": data.provider_type,
                           "base_url": base_url, "model": data.model})
        self.session.commit()
        return self._public(self.get(config_id))

    def clone(self, config_id: int, actor_id: int) -> dict[str, Any]:
        self.get(config_id)
        new_id = self.session.execute(
            text("""INSERT INTO llm_provider_configs
                    (name, provider_type, base_url, model, encrypted_api_key, api_key_suffix,
                     timeout_seconds, created_by, updated_by)
                    SELECT name || ' (bản sao)', provider_type, base_url, model,
                           encrypted_api_key, api_key_suffix, timeout_seconds, :actor, :actor
                    FROM llm_provider_configs WHERE id=:id RETURNING id"""),
            {"id": config_id, "actor": actor_id},
        ).scalar_one()
        self._audit(actor_id, "clone", int(new_id), after={"source_id": config_id})
        self.session.commit()
        return self._public(self.get(int(new_id)))

    def mark_test(self, config_id: int, *, success: bool, mode: str | None, error: str | None) -> dict[str, Any]:
        self.session.execute(
            text("""UPDATE llm_provider_configs SET tested_version=config_version,
                    test_status=:status, structured_output_mode=:mode,
                    last_tested_at=NOW(), last_test_error=:error, updated_at=NOW()
                    WHERE id=:id"""),
            {"id": config_id, "status": "success" if success else "failed",
             "mode": mode, "error": error[:1000] if error else None},
        )
        self.session.commit()
        return self._public(self.get(config_id))

    def activate(self, config_id: int, actor_id: int) -> dict[str, Any]:
        current = self.get(config_id)
        if current["test_status"] != "success" or current["tested_version"] != current["config_version"]:
            raise ConflictError("Provider phải test thành công với phiên bản hiện tại trước khi active.")
        self.session.execute(text("UPDATE llm_provider_configs SET is_active=FALSE WHERE is_active=TRUE"))
        self.session.execute(
            text("UPDATE llm_provider_configs SET is_active=TRUE, updated_by=:actor, updated_at=NOW() WHERE id=:id"),
            {"id": config_id, "actor": actor_id},
        )
        self._audit(actor_id, "activate", config_id)
        self.session.commit()
        return self._public(self.get(config_id))

    def deactivate(self, config_id: int, actor_id: int) -> dict[str, Any]:
        self.get(config_id)
        self.session.execute(
            text("UPDATE llm_provider_configs SET is_active=FALSE, updated_by=:actor, updated_at=NOW() WHERE id=:id"),
            {"id": config_id, "actor": actor_id},
        )
        self._audit(actor_id, "deactivate", config_id)
        self.session.commit()
        return self._public(self.get(config_id))

    def delete(self, config_id: int, actor_id: int) -> None:
        current = self.get(config_id)
        if current["is_active"]:
            raise ConflictError("Không thể xóa provider đang active.")
        count = self.session.execute(text("SELECT COUNT(*) FROM llm_provider_configs")).scalar_one()
        if count <= 1:
            raise ConflictError("Giữ lại cấu hình cuối cùng để tránh quay lại fallback environment.")
        self.session.execute(text("DELETE FROM llm_provider_configs WHERE id=:id"), {"id": config_id})
        self._audit(actor_id, "delete", config_id, before=self._safe_audit(current))
        self.session.commit()

    def _audit(self, actor: int, action: str, entity_id: int, before=None, after=None) -> None:
        self.session.execute(
            text("""INSERT INTO audit_logs
                    (actor_user_id, action, entity_type, entity_id, before_data, after_data)
                    VALUES (:actor, :action, 'llm_provider', :id,
                            CAST(:before AS jsonb), CAST(:after AS jsonb))"""),
            {"actor": actor, "action": action, "id": entity_id,
             "before": json.dumps(before, default=str) if before is not None else None,
             "after": json.dumps(after, default=str) if after is not None else None},
        )

    @staticmethod
    def _safe_audit(data: dict[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in data.items() if key not in {"encrypted_api_key", "api_key"}}

    @staticmethod
    def _public(data: dict[str, Any]) -> dict[str, Any]:
        result = {key: value for key, value in data.items() if key not in {"encrypted_api_key", "api_key"}}
        result["has_api_key"] = bool(data.get("encrypted_api_key") or data.get("api_key_suffix"))
        result["masked_api_key"] = f"••••{data['api_key_suffix']}" if data.get("api_key_suffix") else None
        return result


class AIRequestLogStore:
    def __init__(self, session: Session) -> None:
        self.session = session

    def write(self, **values: Any) -> None:
        self.session.execute(text("DELETE FROM ai_request_logs WHERE expires_at < NOW()"))
        self.session.execute(
            text("""INSERT INTO ai_request_logs
                    (user_id, provider_config_id, feature, provider_type, model,
                     request_data, response_data, status, latency_ms,
                     prompt_tokens, completion_tokens, total_tokens, error_message)
                    VALUES (:user_id, :provider_config_id, :feature, :provider_type, :model,
                            CAST(:request_data AS jsonb), CAST(:response_data AS jsonb), :status,
                            :latency_ms, :prompt_tokens, :completion_tokens, :total_tokens, :error_message)"""),
            {**values,
             "request_data": json.dumps(values["request_data"], ensure_ascii=False, default=str),
             "response_data": json.dumps(values.get("response_data"), ensure_ascii=False, default=str)
                              if values.get("response_data") is not None else None},
        )
        self.session.commit()

    def list(self, *, feature: str | None, status: str | None, user_id: int | None,
             limit: int, offset: int) -> dict[str, Any]:
        self.purge_expired()
        where = ["1=1"]
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        for key, value in (("feature", feature), ("status", status), ("user_id", user_id)):
            if value is not None:
                where.append(f"{key}=:{key}")
                params[key] = value
        clause = " AND ".join(where)
        total = self.session.execute(text(f"SELECT COUNT(*) FROM ai_request_logs WHERE {clause}"), params).scalar_one()
        rows = self.session.execute(
            text(f"""SELECT id, user_id, provider_config_id, feature, provider_type, model,
                            status, latency_ms, prompt_tokens, completion_tokens, total_tokens,
                            error_message, created_at, expires_at
                     FROM ai_request_logs WHERE {clause}
                     ORDER BY created_at DESC LIMIT :limit OFFSET :offset"""), params
        ).mappings().all()
        return {"items": [dict(row) for row in rows], "total": total, "limit": limit, "offset": offset}

    def get(self, log_id: int) -> dict[str, Any]:
        row = self.session.execute(text("SELECT * FROM ai_request_logs WHERE id=:id"), {"id": log_id}).mappings().first()
        if row is None:
            raise NotFoundError("Không tìm thấy AI request log.")
        return dict(row)

    def purge(self, before: datetime, actor_id: int) -> int:
        if before.tzinfo is None:
            before = before.replace(tzinfo=timezone.utc)
        count = self.session.execute(
            text("DELETE FROM ai_request_logs WHERE created_at < :before RETURNING id"), {"before": before}
        ).rowcount
        self.session.execute(
            text("""INSERT INTO audit_logs(actor_user_id, action, entity_type, after_data)
                    VALUES (:actor, 'purge', 'ai_request_log', CAST(:after AS jsonb))"""),
            {"actor": actor_id, "after": json.dumps({"before": before.isoformat(), "deleted": count})},
        )
        self.session.commit()
        return count

    def purge_expired(self) -> int:
        count = self.session.execute(text("DELETE FROM ai_request_logs WHERE expires_at < NOW()")).rowcount
        self.session.commit()
        return count

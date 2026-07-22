from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlmodel import Session

from app.core.database import get_session
from app.core.deps import require_super_admin
from app.modules.ai.admin_schemas import (
    AILogDetail, AILogPage, ProviderItem, ProviderTestResult, ProviderWrite,
    PromptFeature, PurgeLogsRequest, PurgeLogsResponse, SystemPromptItem,
    SystemPromptWrite,
)
from app.modules.ai.client import OpenAICompatibleAIClient
from app.modules.ai.prompt_store import SystemPromptStore
from app.modules.ai.provider_store import AIRequestLogStore, ProviderConfigStore
from app.modules.identity.domain import UserEntity


router = APIRouter(prefix="/api/admin/ai", tags=["admin-ai"])


def get_store(session: Session = Depends(get_session)) -> ProviderConfigStore:
    return ProviderConfigStore(session)


def get_prompt_store(session: Session = Depends(get_session)) -> SystemPromptStore:
    return SystemPromptStore(session)


@router.get("/providers", response_model=list[ProviderItem])
def list_providers(store: ProviderConfigStore = Depends(get_store),
                   _: UserEntity = Depends(require_super_admin)):
    return store.list()


@router.post("/providers", response_model=ProviderItem, status_code=status.HTTP_201_CREATED)
def create_provider(data: ProviderWrite, store: ProviderConfigStore = Depends(get_store),
                    user: UserEntity = Depends(require_super_admin)):
    return store.create(data, user.id)


@router.put("/providers/{config_id}", response_model=ProviderItem)
def update_provider(config_id: int, data: ProviderWrite,
                    store: ProviderConfigStore = Depends(get_store),
                    user: UserEntity = Depends(require_super_admin)):
    return store.update(config_id, data, user.id)


@router.delete("/providers/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_provider(config_id: int, store: ProviderConfigStore = Depends(get_store),
                    user: UserEntity = Depends(require_super_admin)):
    store.delete(config_id, user.id)


@router.post("/providers/{config_id}/clone", response_model=ProviderItem)
def clone_provider(config_id: int, store: ProviderConfigStore = Depends(get_store),
                   user: UserEntity = Depends(require_super_admin)):
    return store.clone(config_id, user.id)


def _client(store: ProviderConfigStore, config_id: int, mode: str) -> OpenAICompatibleAIClient:
    data = store.get(config_id, include_secret=True)
    return OpenAICompatibleAIClient(
        base_url=data["base_url"], model=data["model"], api_key=data.get("api_key"),
        timeout_seconds=float(data["timeout_seconds"]), structured_output_mode=mode,
        native_web_search_enabled=bool(data.get("native_web_search_enabled")),
    )


@router.post("/providers/{config_id}/discover-models", response_model=list[str])
def discover_models(config_id: int, store: ProviderConfigStore = Depends(get_store),
                    _: UserEntity = Depends(require_super_admin)):
    return _client(store, config_id, "json_schema").list_models()


@router.post("/providers/{config_id}/test", response_model=ProviderTestResult)
def test_provider(config_id: int, store: ProviderConfigStore = Depends(get_store),
                  _: UserEntity = Depends(require_super_admin)):
    data = store.get(config_id)
    modes = ["json_object"] if data["provider_type"] == "deepseek" else ["json_schema", "json_object"]
    models: list[str] = []
    errors: list[str] = []
    for mode in modes:
        try:
            client = _client(store, config_id, mode)
            try:
                models = client.list_models()
            except Exception:
                models = []
            client.complete_text([{"role": "user", "content": "Trả lời đúng một từ: OK"}])
            result = client.complete_json(
                [{"role": "user", "content": "Trả JSON có trường ok bằng true."}],
                schema_name="provider_health", json_schema={
                    "type": "object", "properties": {"ok": {"type": "boolean"}},
                    "required": ["ok"], "additionalProperties": False,
                },
            )
            if result.get("ok") is not True:
                raise ValueError("Structured output không khớp schema kiểm tra.")
            if data.get("native_web_search_enabled"):
                _, citations = client.complete_grounded_text([
                    {"role": "user", "content": "Nêu một khuyến nghị dinh dưỡng phổ thông hiện hành và dẫn nguồn."}
                ])
                if not citations:
                    raise ValueError("Web search không trả citation hợp lệ.")
            return ProviderTestResult(provider=store.mark_test(config_id, success=True, mode=mode, error=None), models=models)
        except Exception as exc:
            errors.append(f"{mode}: {exc}")
    provider = store.mark_test(config_id, success=False, mode=None, error="; ".join(errors))
    return ProviderTestResult(provider=provider, models=models)


@router.post("/providers/{config_id}/activate", response_model=ProviderItem)
def activate_provider(config_id: int, store: ProviderConfigStore = Depends(get_store),
                      user: UserEntity = Depends(require_super_admin)):
    return store.activate(config_id, user.id)


@router.post("/providers/{config_id}/deactivate", response_model=ProviderItem)
def deactivate_provider(config_id: int, store: ProviderConfigStore = Depends(get_store),
                        user: UserEntity = Depends(require_super_admin)):
    return store.deactivate(config_id, user.id)


@router.get("/prompts", response_model=list[SystemPromptItem])
def list_system_prompts(store: SystemPromptStore = Depends(get_prompt_store),
                        _: UserEntity = Depends(require_super_admin)):
    return store.list()


@router.put("/prompts/{feature}", response_model=SystemPromptItem)
def update_system_prompt(feature: PromptFeature, data: SystemPromptWrite,
                         store: SystemPromptStore = Depends(get_prompt_store),
                         user: UserEntity = Depends(require_super_admin)):
    return store.update(feature, data.content, user.id)


@router.delete("/prompts/{feature}", response_model=SystemPromptItem)
def reset_system_prompt(feature: PromptFeature,
                        store: SystemPromptStore = Depends(get_prompt_store),
                        user: UserEntity = Depends(require_super_admin)):
    return store.reset(feature, user.id)


@router.get("/logs", response_model=AILogPage)
def list_logs(feature: str | None = None, status_filter: str | None = Query(None, alias="status"),
              user_id: int | None = None, limit: int = Query(20, ge=1, le=100),
              offset: int = Query(0, ge=0), session: Session = Depends(get_session),
              _: UserEntity = Depends(require_super_admin)):
    return AIRequestLogStore(session).list(feature=feature, status=status_filter, user_id=user_id,
                                           limit=limit, offset=offset)


@router.get("/logs/{log_id}", response_model=AILogDetail)
def get_log(log_id: int, session: Session = Depends(get_session),
            _: UserEntity = Depends(require_super_admin)):
    return AIRequestLogStore(session).get(log_id)


@router.post("/logs/purge", response_model=PurgeLogsResponse)
def purge_logs(data: PurgeLogsRequest, session: Session = Depends(get_session),
               user: UserEntity = Depends(require_super_admin)):
    return {"deleted": AIRequestLogStore(session).purge(data.before, user.id)}

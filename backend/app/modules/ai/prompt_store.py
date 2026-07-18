from __future__ import annotations

import json
from typing import Any

from sqlalchemy import text
from sqlmodel import Session

from app.modules.ai.prompts import DEFAULT_SYSTEM_PROMPTS, PROMPT_FEATURES


class SystemPromptStore:
    """Global per-feature prompt overrides with code defaults as the fallback."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def list(self) -> list[dict[str, Any]]:
        rows = self.session.execute(
            text("""SELECT feature, content, updated_at
                    FROM ai_system_prompts""")
        ).mappings().all()
        overrides = {str(row["feature"]): dict(row) for row in rows}
        return [self._item(feature, overrides.get(feature)) for feature in PROMPT_FEATURES]

    def get_effective(self, feature: str) -> str:
        row = self.session.execute(
            text("SELECT content FROM ai_system_prompts WHERE feature=:feature"),
            {"feature": feature},
        ).mappings().first()
        if row is not None:
            return str(row["content"])
        return DEFAULT_SYSTEM_PROMPTS[feature]

    def update(self, feature: str, content: str, actor_id: int) -> dict[str, Any]:
        before = self._get_override(feature)
        self.session.execute(
            text("""INSERT INTO ai_system_prompts (feature, content, updated_by)
                    VALUES (:feature, :content, :actor)
                    ON CONFLICT (feature) DO UPDATE SET
                        content=EXCLUDED.content,
                        updated_by=EXCLUDED.updated_by,
                        updated_at=NOW()"""),
            {"feature": feature, "content": content, "actor": actor_id},
        )
        self._audit(
            actor_id,
            "update",
            before={"feature": feature, "content": self._effective_content(feature, before)},
            after={"feature": feature, "content": content},
        )
        self.session.commit()
        return self._item(feature, self._get_override(feature))

    def reset(self, feature: str, actor_id: int) -> dict[str, Any]:
        before = self._get_override(feature)
        if before is not None:
            self.session.execute(
                text("DELETE FROM ai_system_prompts WHERE feature=:feature"),
                {"feature": feature},
            )
            self._audit(
                actor_id,
                "reset",
                before={"feature": feature, "content": str(before["content"])},
                after={"feature": feature, "content": DEFAULT_SYSTEM_PROMPTS[feature]},
            )
            self.session.commit()
        return self._item(feature, None)

    def _get_override(self, feature: str) -> dict[str, Any] | None:
        row = self.session.execute(
            text("""SELECT feature, content, updated_at
                    FROM ai_system_prompts WHERE feature=:feature"""),
            {"feature": feature},
        ).mappings().first()
        return dict(row) if row is not None else None

    @staticmethod
    def _effective_content(feature: str, row: dict[str, Any] | None) -> str:
        return str(row["content"]) if row is not None else DEFAULT_SYSTEM_PROMPTS[feature]

    @classmethod
    def _item(cls, feature: str, row: dict[str, Any] | None) -> dict[str, Any]:
        return {
            "feature": feature,
            "content": cls._effective_content(feature, row),
            "is_custom": row is not None,
            "updated_at": row.get("updated_at") if row is not None else None,
        }

    def _audit(self, actor_id: int, action: str, *, before: dict, after: dict) -> None:
        self.session.execute(
            text("""INSERT INTO audit_logs
                    (actor_user_id, action, entity_type, before_data, after_data)
                    VALUES (:actor, :action, 'ai_system_prompt',
                            CAST(:before AS jsonb), CAST(:after AS jsonb))"""),
            {
                "actor": actor_id,
                "action": action,
                "before": json.dumps(before, ensure_ascii=False),
                "after": json.dumps(after, ensure_ascii=False),
            },
        )

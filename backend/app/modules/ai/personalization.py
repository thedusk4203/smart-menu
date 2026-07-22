from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from sqlalchemy import text
from sqlmodel import Session

from app.core.exceptions import AuthorizationError, ValidationAppError


ChatMode = Literal["general", "meal_advice", "health_reference"]
AI_NOTICE_VERSION = "2026-07-22"


@dataclass(frozen=True, slots=True)
class AuthenticatedAIRequestScope:
    """Identity boundary for AI reads; always constructed from the access token."""

    user_id: int


class AIPreferenceStore:
    """Writes only AI consent state, never profile, menu or inventory data."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def _set_actor(self, scope: AuthenticatedAIRequestScope) -> None:
        self.session.execute(
            text("SELECT set_config('app.current_user_id', :actor_id, true)"),
            {"actor_id": str(scope.user_id)},
        )

    def get(self, scope: AuthenticatedAIRequestScope) -> dict[str, Any]:
        self._set_actor(scope)
        row = self.session.execute(
            text(
                """SELECT personalization_enabled, notice_version, consented_at, updated_at
                     FROM user_ai_preferences WHERE user_id=:actor_id"""
            ),
            {"actor_id": scope.user_id},
        ).mappings().first()
        if row is None:
            return {
                "personalization_enabled": False,
                "notice_version": AI_NOTICE_VERSION,
                "consented_at": None,
                "updated_at": None,
            }
        result = dict(row)
        if result["notice_version"] != AI_NOTICE_VERSION:
            result["personalization_enabled"] = False
            result["notice_version"] = AI_NOTICE_VERSION
            result["consented_at"] = None
        return result

    def update(
        self,
        scope: AuthenticatedAIRequestScope,
        *,
        personalization_enabled: bool,
        notice_version: str,
    ) -> dict[str, Any]:
        self._set_actor(scope)
        if notice_version != AI_NOTICE_VERSION:
            raise ValidationAppError(
                "Phiên bản thông báo quyền riêng tư đã thay đổi. Hãy tải lại trang.",
                code="AI_NOTICE_VERSION_STALE",
            )
        row = self.session.execute(
            text(
                """INSERT INTO user_ai_preferences
                       (user_id, personalization_enabled, notice_version, consented_at, updated_at)
                   VALUES (:actor_id, :enabled, :notice_version,
                           CASE WHEN :enabled THEN NOW() ELSE NULL END, NOW())
                   ON CONFLICT (user_id) DO UPDATE SET
                       personalization_enabled=EXCLUDED.personalization_enabled,
                       notice_version=EXCLUDED.notice_version,
                       consented_at=CASE
                           WHEN EXCLUDED.personalization_enabled THEN NOW() ELSE NULL END,
                       updated_at=NOW()
                   RETURNING personalization_enabled, notice_version, consented_at, updated_at"""
            ),
            {
                "actor_id": scope.user_id,
                "enabled": personalization_enabled,
                "notice_version": notice_version,
            },
        ).mappings().one()
        self.session.execute(
            text(
                """INSERT INTO ai_consent_events
                       (user_id, personalization_enabled, notice_version)
                   VALUES (:actor_id, :enabled, :notice_version)"""
            ),
            {
                "actor_id": scope.user_id,
                "enabled": personalization_enabled,
                "notice_version": notice_version,
            },
        )
        self.session.commit()
        return dict(row)

    def require_enabled(self, scope: AuthenticatedAIRequestScope) -> None:
        if not self.get(scope)["personalization_enabled"]:
            raise AuthorizationError(
                "Bạn chưa cho phép Menuto sử dụng hồ sơ cá nhân.",
                code="AI_PERSONALIZATION_CONSENT_REQUIRED",
                user_message="Hãy bật quyền cá nhân hoá trong Hồ sơ để dùng chế độ này.",
            )


class AIContextReader:
    """Purpose-limited, read-only projection for the authenticated actor."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def build(
        self, scope: AuthenticatedAIRequestScope, *, mode: ChatMode
    ) -> dict[str, Any]:
        if mode == "general":
            return {}
        self.session.execute(
            text("SELECT set_config('app.current_user_id', :actor_id, true)"),
            {"actor_id": str(scope.user_id)},
        )
        profile = self.session.execute(
            text(
                """SELECT gender, age, height_cm, weight_kg, activity_level, goal,
                          meals_per_day, daily_calorie_target, daily_budget
                     FROM user_profiles
                    WHERE user_id=:actor_id"""
            ),
            {"actor_id": scope.user_id},
        ).mappings().first()
        if profile is None:
            raise ValidationAppError(
                "Chưa có hồ sơ để Menuto cá nhân hoá.",
                code="AI_PROFILE_REQUIRED",
                user_message="Hãy hoàn thiện Hồ sơ trước khi dùng tư vấn cá nhân hoá.",
            )
        if mode == "health_reference" and (
            profile["age"] is None or int(profile["age"]) < 18
        ):
            raise AuthorizationError(
                "Chế độ tham khảo sức khoẻ chỉ dành cho người dùng từ 18 tuổi.",
                code="AI_HEALTH_AGE_RESTRICTED",
                user_message="Chế độ tham khảo sức khoẻ yêu cầu hồ sơ có tuổi từ 18 trở lên.",
            )

        exclusions = self.session.execute(
            text(
                """SELECT i.name AS ingredient_name, e.reason
                     FROM user_excluded_ingredients e
                     JOIN ingredients i ON i.id=e.ingredient_id
                    WHERE e.user_id=:actor_id
                    ORDER BY i.name"""
            ),
            {"actor_id": scope.user_id},
        ).mappings().all()
        common = {
            "goal": str(profile["goal"]),
            "activity_level": str(profile["activity_level"]),
            "meals_per_day": profile["meals_per_day"],
            "daily_calorie_target": profile["daily_calorie_target"],
            "daily_budget": profile["daily_budget"],
            "excluded_ingredients": [
                {"name": row["ingredient_name"], "reason": str(row["reason"])}
                for row in exclusions
            ],
        }
        if mode == "health_reference":
            common.update(
                {
                    "age": profile["age"],
                    "gender": str(profile["gender"]) if profile["gender"] else None,
                    "height_cm": profile["height_cm"],
                    "weight_kg": profile["weight_kg"],
                }
            )
        return common


class ActiveDishTagReader:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_names(self) -> list[str]:
        return list(
            self.session.execute(
                text(
                    """SELECT name FROM tag_catalog
                        WHERE entity_type='dish' AND is_active=TRUE
                        ORDER BY name"""
                )
            ).scalars().all()
        )

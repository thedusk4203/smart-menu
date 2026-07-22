from __future__ import annotations

from uuid import uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.core.database import engine
from app.core.exceptions import AuthorizationError
from app.modules.ai.personalization import (
    AIContextReader, AIPreferenceStore, AuthenticatedAIRequestScope,
)
from app.modules.ai.conversation_store import ConversationStore
from app.modules.ai.schemas import ChatRequest
from sqlmodel import Session


def _create_two_users() -> tuple[int, int]:
    with engine.begin() as connection:
        ids = []
        for suffix in ("a", "b"):
            user_id = int(
                connection.execute(
                    text(
                        """INSERT INTO users (email, hashed_password, role)
                           VALUES (:email, 'test', 'user') RETURNING id"""
                    ),
                    {"email": f"ai-scope-{suffix}-{uuid4()}@example.com"},
                ).scalar_one()
            )
            connection.execute(
                text(
                    """INSERT INTO user_profiles
                           (user_id, full_name, activity_level, goal, meals_per_day)
                       VALUES (:user_id, :name, 'moderate', 'maintain', 3)"""
                ),
                {"user_id": user_id, "name": f"User {suffix.upper()}"},
            )
            ids.append(user_id)
    return ids[0], ids[1]


def _cleanup_users(*user_ids: int) -> None:
    with engine.begin() as connection:
        connection.execute(
            text("DELETE FROM users WHERE id = ANY(:ids)"), {"ids": list(user_ids)}
        )


def _set_role_or_skip(connection, role: str) -> None:
    try:
        connection.execute(text(f"SET ROLE {role}"))
    except DBAPIError as exc:  # pragma: no cover - non-superuser CI database
        connection.rollback()
        pytest.skip(f"Database test user cannot SET ROLE {role}: {exc}")


def test_chat_contract_rejects_identity_and_arbitrary_context():
    for field, value in (
        ("user_id", 999),
        ("context", {"user_id": 999}),
        ("history", []),
    ):
        with pytest.raises(ValidationError, match=field):
            ChatRequest.model_validate({"message": "Xin chào", field: value})


def test_context_database_role_sees_only_actor_and_cannot_write_business_data():
    user_a, user_b = _create_two_users()
    connection = engine.connect()
    try:
        transaction = connection.begin()
        _set_role_or_skip(connection, "menuto_ai_context_reader")
        connection.execute(
            text("SELECT set_config('app.current_user_id', :actor, true)"),
            {"actor": str(user_a)},
        )
        visible = connection.execute(
            text("SELECT user_id FROM user_profiles ORDER BY user_id")
        ).scalars().all()
        assert visible == [user_a]
        with pytest.raises(DBAPIError):
            connection.execute(
                text("UPDATE user_profiles SET full_name='changed' WHERE user_id=:id"),
                {"id": user_a},
            )
        transaction.rollback()
        connection.execute(text("RESET ROLE"))
        connection.commit()

        with engine.connect() as verify:
            assert verify.execute(
                text("SELECT full_name FROM user_profiles WHERE user_id=:id"),
                {"id": user_a},
            ).scalar_one() == "User A"
    finally:
        try:
            connection.execute(text("RESET ROLE"))
            connection.commit()
        except DBAPIError:
            connection.rollback()
        connection.close()
        _cleanup_users(user_a, user_b)


def test_actor_setting_is_transaction_local_and_state_role_cannot_cross_users():
    user_a, user_b = _create_two_users()
    connection = engine.connect()
    try:
        transaction = connection.begin()
        _set_role_or_skip(connection, "menuto_ai_state_writer")
        connection.execute(
            text("SELECT set_config('app.current_user_id', :actor, true)"),
            {"actor": str(user_a)},
        )
        with pytest.raises(DBAPIError):
            connection.execute(
                text("UPDATE user_profiles SET full_name='forbidden' WHERE user_id=:id"),
                {"id": user_a},
            )
        transaction.rollback()
        connection.execute(text("RESET ROLE"))
        connection.commit()

        transaction = connection.begin()
        _set_role_or_skip(connection, "menuto_ai_state_writer")
        connection.execute(
            text("SELECT set_config('app.current_user_id', :actor, true)"),
            {"actor": str(user_a)},
        )
        connection.execute(
            text(
                """INSERT INTO user_ai_preferences
                       (user_id, personalization_enabled, notice_version)
                   VALUES (:id, TRUE, '2026-07-22')"""
            ),
            {"id": user_a},
        )
        with pytest.raises(DBAPIError):
            connection.execute(
                text(
                    """INSERT INTO user_ai_preferences
                           (user_id, personalization_enabled, notice_version)
                       VALUES (:id, TRUE, '2026-07-22')"""
                ),
                {"id": user_b},
            )
        transaction.rollback()
        connection.execute(text("RESET ROLE"))
        connection.commit()

        transaction = connection.begin()
        _set_role_or_skip(connection, "menuto_ai_context_reader")
        assert connection.execute(
            text("SELECT current_setting('app.current_user_id', TRUE)")
        ).scalar_one() == ""
        assert connection.execute(text("SELECT user_id FROM user_profiles")).all() == []
        transaction.rollback()
    finally:
        try:
            connection.execute(text("RESET ROLE"))
            connection.commit()
        except DBAPIError:
            connection.rollback()
        connection.close()
        _cleanup_users(user_a, user_b)


def test_personal_context_is_purpose_limited_and_health_requires_adult_profile():
    user_a, user_b = _create_two_users()
    with engine.begin() as connection:
        connection.execute(
            text("UPDATE user_profiles SET age=17, gender='female', height_cm=160, weight_kg=50 WHERE user_id=:id"),
            {"id": user_a},
        )
    try:
        with Session(engine) as session:
            reader = AIContextReader(session)
            meal_context = reader.build(
                AuthenticatedAIRequestScope(user_a), mode="meal_advice"
            )
            assert "age" not in meal_context
            assert "full_name" not in meal_context
            assert "user_id" not in meal_context
            with pytest.raises(AuthorizationError, match="18"):
                reader.build(
                    AuthenticatedAIRequestScope(user_a), mode="health_reference"
                )

        with engine.begin() as connection:
            connection.execute(
                text("UPDATE user_profiles SET age=30 WHERE user_id=:id"), {"id": user_a}
            )
        with Session(engine) as session:
            health_context = AIContextReader(session).build(
                AuthenticatedAIRequestScope(user_a), mode="health_reference"
            )
            assert health_context["age"] == 30
            assert health_context["gender"] == "female"
            assert "full_name" not in health_context
    finally:
        _cleanup_users(user_a, user_b)


def test_ai_consent_defaults_off_and_updates_only_authenticated_actor():
    user_a, user_b = _create_two_users()
    try:
        with Session(engine) as session:
            store = AIPreferenceStore(session)
            assert store.get(AuthenticatedAIRequestScope(user_a))["personalization_enabled"] is False
            updated = store.update(
                AuthenticatedAIRequestScope(user_a),
                personalization_enabled=True,
                notice_version="2026-07-22",
            )
            assert updated["personalization_enabled"] is True
            assert store.get(AuthenticatedAIRequestScope(user_b))["personalization_enabled"] is False
    finally:
        _cleanup_users(user_a, user_b)


def test_state_role_can_persist_only_authenticated_conversation_state():
    user_a, user_b = _create_two_users()
    try:
        with Session(engine) as session:
            _set_role_or_skip(session, "menuto_ai_state_writer")
            store = ConversationStore(session, actor_id=user_a)
            conversation_id, turn = store.start_turn(
                user_id=user_a, message="Tạo thực đơn", conversation_id=None
            )
            assert turn["status"] == "pending"
            store.complete_turn(
                conversation_id=conversation_id,
                turn_id=int(turn["id"]),
                assistant_content="Đây là gợi ý.",
            )
            assert store.list_for_user(user_a)[0]["id"] == conversation_id
            assert store.list_for_user(user_b) == []
            session.execute(text("RESET ROLE"))
            session.commit()
    finally:
        _cleanup_users(user_a, user_b)

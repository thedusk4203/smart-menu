from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.modules.identity.domain import UserEntity
from app.modules.identity.router import register
from app.modules.identity.schemas import RegisterRequest
from app.shared.enums import UserRole


class FakeCreateUserUseCase:
    def __init__(self) -> None:
        self.arguments: tuple[str, str, UserRole] | None = None

    def execute(self, email: str, password: str, role: UserRole) -> UserEntity:
        self.arguments = (email, password, role)
        return UserEntity(id=42, email=email, hashed_password="hash", role=role)


class FakeProfileUseCase:
    def __init__(self) -> None:
        self.arguments: tuple[int, str | None] | None = None

    def execute(self, user_id: int, full_name: str | None):
        self.arguments = (user_id, full_name)


def test_public_registration_always_creates_standard_user():
    users = FakeCreateUserUseCase()
    profiles = FakeProfileUseCase()

    response = register(
        RegisterRequest(email="new@example.com", password="strong-password", full_name="New User"),
        users,
        profiles,
    )

    assert users.arguments == ("new@example.com", "strong-password", UserRole.USER)
    assert profiles.arguments == (42, "New User")
    assert response["role"] == UserRole.USER


def test_registration_requires_a_long_enough_password():
    with pytest.raises(ValidationError):
        RegisterRequest(email="new@example.com", password="short")

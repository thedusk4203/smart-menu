from __future__ import annotations

import pytest

from app.core.security import verify_password
from app.modules.identity.domain import UserEntity
from app.modules.identity.exceptions import (
    GoogleAuthenticationError,
    GoogleAuthenticationNotConfiguredError,
)
from app.modules.identity.google_verifier import GoogleTokenVerifier
from app.modules.identity.router import google_login
from app.modules.identity.schemas import GoogleLoginRequest
from app.modules.identity.use_cases import GoogleIdentity, GoogleLoginResult, GoogleLoginUseCase
from app.shared.enums import UserRole


class FakeUserRepository:
    def __init__(self, user: UserEntity | None = None) -> None:
        self.user = user
        self.saved: list[UserEntity] = []

    def get_by_email(self, _email: str) -> UserEntity | None:
        return self.user

    def save(self, user: UserEntity) -> UserEntity:
        saved = UserEntity(id=42, **{key: value for key, value in user.__dict__.items() if key != "id"})
        self.user = saved
        self.saved.append(saved)
        return saved


class FakeGoogleVerifier:
    def __init__(self, identity: GoogleIdentity) -> None:
        self.identity = identity

    def verify(self, _credential: str) -> GoogleIdentity:
        return self.identity


def test_google_login_creates_a_standard_user_with_unusable_random_password():
    repo = FakeUserRepository()
    use_case = GoogleLoginUseCase(
        repo,
        FakeGoogleVerifier(GoogleIdentity(email="new.user@gmail.com", full_name="New User")),
    )

    result = use_case.execute("google-id-token")

    assert result.is_new_user is True
    assert result.user_id == 42
    assert result.full_name == "New User"
    assert result.access_token
    assert len(repo.saved) == 1
    assert repo.saved[0].email == "new.user@gmail.com"
    assert repo.saved[0].role is UserRole.USER
    assert not verify_password("google-id-token", repo.saved[0].hashed_password)


def test_google_login_uses_the_existing_account_with_the_same_email():
    existing = UserEntity(
        id=7,
        email="existing@gmail.com",
        hashed_password="already-hashed",
        role=UserRole.ADMIN,
    )
    repo = FakeUserRepository(existing)
    use_case = GoogleLoginUseCase(
        repo,
        FakeGoogleVerifier(GoogleIdentity(email="existing@gmail.com", full_name="Other Name")),
    )

    result = use_case.execute("google-id-token")

    assert result.is_new_user is False
    assert result.user_id == 7
    assert repo.saved == []


def test_google_verifier_rejects_non_gmail_and_unverified_email(monkeypatch):
    monkeypatch.setattr("app.modules.identity.google_verifier.settings.google_client_id", "client-id")
    monkeypatch.setattr(
        "app.modules.identity.google_verifier.id_token.verify_oauth2_token",
        lambda *_args: {"email": "person@company.com", "email_verified": True},
    )
    with pytest.raises(GoogleAuthenticationError, match="Chỉ hỗ trợ"):
        GoogleTokenVerifier().verify("credential")

    monkeypatch.setattr(
        "app.modules.identity.google_verifier.id_token.verify_oauth2_token",
        lambda *_args: {"email": "person@gmail.com", "email_verified": False},
    )
    with pytest.raises(GoogleAuthenticationError, match="chưa xác minh"):
        GoogleTokenVerifier().verify("credential")


def test_google_verifier_requires_configuration(monkeypatch):
    monkeypatch.setattr("app.modules.identity.google_verifier.settings.google_client_id", None)

    with pytest.raises(GoogleAuthenticationNotConfiguredError):
        GoogleTokenVerifier().verify("credential")


def test_google_login_route_creates_a_profile_only_for_a_new_user():
    class FakeGoogleLoginUseCase:
        def execute(self, _credential: str) -> GoogleLoginResult:
            return GoogleLoginResult("token", True, 42, "New User")

    class FakeProfileUseCase:
        arguments: tuple[int, str | None] | None = None

        def execute(self, user_id: int, full_name: str | None):
            self.arguments = (user_id, full_name)

    profiles = FakeProfileUseCase()
    response = google_login(
        GoogleLoginRequest(credential="token"),
        FakeGoogleLoginUseCase(),
        profiles,
    )

    assert response.access_token == "token"
    assert profiles.arguments == (42, "New User")

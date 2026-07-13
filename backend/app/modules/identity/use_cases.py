from __future__ import annotations

from dataclasses import dataclass
import secrets

from app.core.security import create_access_token, hash_password
from app.modules.identity.domain import UserEntity
from app.modules.identity.exceptions import EmailAlreadyExistsError, UserNotFoundError
from app.modules.identity.ports import UserRepositoryPort
from app.shared.enums import UserRole


@dataclass(frozen=True)
class GoogleIdentity:
    email: str
    full_name: str | None


@dataclass(frozen=True)
class GoogleLoginResult:
    access_token: str
    is_new_user: bool
    user_id: int
    full_name: str | None


class ListUsersUseCase:
    def __init__(self, repo: UserRepositoryPort) -> None:
        self._repo = repo

    def execute(self, limit: int, offset: int) -> list[UserEntity]:
        return self._repo.list_all(limit, offset)


class GetUserUseCase:
    def __init__(self, repo: UserRepositoryPort) -> None:
        self._repo = repo

    def execute(self, user_id: int) -> UserEntity:
        user = self._repo.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(user_id)
        return user


class CreateUserUseCase:
    def __init__(self, repo: UserRepositoryPort) -> None:
        self._repo = repo

    def execute(self, email: str, password: str, role: UserRole = UserRole.USER) -> UserEntity:
        if self._repo.get_by_email(email) is not None:
            raise EmailAlreadyExistsError(email)
        user = UserEntity(id=None, email=email, hashed_password=hash_password(password), role=role)
        return self._repo.save(user)


class UpdateUserUseCase:
    def __init__(self, repo: UserRepositoryPort) -> None:
        self._repo = repo

    def execute(self, user_id: int, **changes) -> UserEntity:
        user = self._repo.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(user_id)
        if "password" in changes:
            changes["hashed_password"] = hash_password(changes.pop("password"))
        if "email" in changes and changes["email"] != user.email:
            if self._repo.get_by_email(changes["email"]) is not None:
                raise EmailAlreadyExistsError(changes["email"])
        updated = UserEntity(**{**user.__dict__, **changes})
        return self._repo.save(updated)


class DeleteUserUseCase:
    def __init__(self, repo: UserRepositoryPort) -> None:
        self._repo = repo

    def execute(self, user_id: int) -> None:
        if self._repo.get_by_id(user_id) is None:
            raise UserNotFoundError(user_id)
        self._repo.delete(user_id)

class LoginUseCase:
    """Xác thực email/password, trả về JWT access token."""
    def __init__(self, repo: UserRepositoryPort) -> None:
        self._repo = repo

    def execute(self, email: str, password: str) -> str:
        from app.core.security import create_access_token, verify_password
        from app.core.exceptions import AppException

        class _AuthError(AppException):
            status_code = 401

        user = self._repo.get_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            raise _AuthError("Email hoặc mật khẩu không đúng")
        if not user.is_active:
            raise _AuthError("Tài khoản đã bị khoá")
        return create_access_token(user.id, user.role.value)


class GoogleLoginUseCase:
    """Đăng nhập Google sau khi token đã được verifier xác minh."""

    def __init__(self, repo: UserRepositoryPort, verifier) -> None:
        self._repo = repo
        self._verifier = verifier

    def execute(self, credential: str) -> GoogleLoginResult:
        identity: GoogleIdentity = self._verifier.verify(credential)
        user = self._repo.get_by_email(identity.email)
        is_new_user = user is None
        if user is None:
            user = self._repo.save(
                UserEntity(
                    id=None,
                    email=identity.email,
                    hashed_password=hash_password(secrets.token_urlsafe(32)),
                    role=UserRole.USER,
                )
            )
        if not user.is_active:
            from app.core.exceptions import AppException

            class _AuthError(AppException):
                status_code = 401

            raise _AuthError("Tài khoản đã bị khoá")
        return GoogleLoginResult(
            access_token=create_access_token(user.id, user.role.value),
            is_new_user=is_new_user,
            user_id=user.id,
            full_name=identity.full_name,
        )

# File: backend/app/modules/identity/use_cases.py
# Application-layer use cases for the identity module (account CRUD).
# Login/Register/Logout (JWT-based authentication) will be added here as a
# separate set of use cases once the team starts the auth feature.
from __future__ import annotations

from app.core.security import hash_password
from app.modules.identity.domain import UserEntity
from app.modules.identity.exceptions import EmailAlreadyExistsError, UserNotFoundError
from app.modules.identity.ports import UserRepositoryPort
from app.shared.enums import UserRole


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

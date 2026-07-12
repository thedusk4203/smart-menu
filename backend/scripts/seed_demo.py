from __future__ import annotations

import os

from sqlmodel import Session

from app.core.database import engine
from app.modules.identity.repository import SqlUserRepository
from app.modules.identity.use_cases import CreateUserUseCase
from app.modules.profiles.repository import SqlUserProfileRepository
from app.modules.profiles.use_cases import CreateEmptyProfileUseCase
from app.shared.enums import UserRole


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} phải được cấu hình khi DEMO_SEED=true.")
    return value


def _seed_account(
    repository: SqlUserRepository,
    users: CreateUserUseCase,
    profiles: CreateEmptyProfileUseCase,
    *,
    email: str,
    password: str,
    role: UserRole,
    full_name: str,
) -> None:
    if repository.get_by_email(email) is not None:
        return
    user = users.execute(email, password, role)
    profiles.execute(user.id, full_name)


def main() -> None:
    if os.getenv("DEMO_SEED", "false").strip().lower() not in {"1", "true", "yes", "on"}:
        return
    with Session(engine) as session:
        user_repository = SqlUserRepository(session)
        users = CreateUserUseCase(user_repository)
        profiles = CreateEmptyProfileUseCase(SqlUserProfileRepository(session))
        _seed_account(
            user_repository,
            users,
            profiles,
            email=_required("DEMO_ADMIN_EMAIL"),
            password=_required("DEMO_ADMIN_PASSWORD"),
            role=UserRole.ADMIN,
            full_name="Quản trị viên Demo",
        )
        _seed_account(
            user_repository,
            users,
            profiles,
            email=_required("DEMO_USER_EMAIL"),
            password=_required("DEMO_USER_PASSWORD"),
            role=UserRole.USER,
            full_name="Người dùng Demo",
        )


if __name__ == "__main__":
    main()

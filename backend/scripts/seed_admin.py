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


def main() -> None:
    if os.getenv("DEMO_SEED", "false").strip().lower() not in {"1", "true", "yes", "on"}:
        return

    email = _required("DEMO_ADMIN_EMAIL")
    password = _required("DEMO_ADMIN_PASSWORD")

    with Session(engine) as session:
        user_repository = SqlUserRepository(session)
        if user_repository.get_by_email(email) is not None:
            return

        user = CreateUserUseCase(user_repository).execute(email, password, UserRole.ADMIN)
        CreateEmptyProfileUseCase(SqlUserProfileRepository(session)).execute(
            user.id,
            "Quản trị viên",
        )


if __name__ == "__main__":
    main()

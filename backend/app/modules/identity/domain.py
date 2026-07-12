# Domain entity for a user account. Pure Python — no FastAPI/SQLModel.
from __future__ import annotations

from dataclasses import dataclass

from app.shared.enums import UserRole


@dataclass(frozen=True)
class UserEntity:
    """A user account. hashed_password is the bcrypt hash, never plaintext."""
    id: int | None
    email: str
    hashed_password: str
    role: UserRole = UserRole.USER
    is_active: bool = True

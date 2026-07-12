# Domain exceptions for the identity module.
from __future__ import annotations

from app.core.exceptions import ConflictError, NotFoundError


class UserNotFoundError(NotFoundError):
    def __init__(self, user_id: int) -> None:
        super().__init__(f"Không tìm thấy tài khoản id={user_id}")


class EmailAlreadyExistsError(ConflictError):
    def __init__(self, email: str) -> None:
        super().__init__(f"Email '{email}' đã được sử dụng")

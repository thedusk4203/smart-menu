# Domain exceptions for the identity module.
from __future__ import annotations

from app.core.exceptions import AppException, ConflictError, NotFoundError


class UserNotFoundError(NotFoundError):
    def __init__(self, user_id: int) -> None:
        super().__init__(
            f"Không tìm thấy tài khoản id={user_id}",
            code="USER_NOT_FOUND",
            user_message="Không tìm thấy tài khoản này.",
            details={"user_id": user_id},
        )


class EmailAlreadyExistsError(ConflictError):
    def __init__(self, email: str) -> None:
        super().__init__(
            f"Email '{email}' đã được sử dụng",
            code="EMAIL_ALREADY_EXISTS",
            user_message="Email này đã được sử dụng. Hãy đăng nhập hoặc chọn email khác.",
            fields={"email": "Email này đã được sử dụng."},
        )


class GoogleAuthenticationError(AppException):
    status_code = 401
    code = "GOOGLE_AUTH_FAILED"
    user_message = "Không thể đăng nhập bằng Google. Hãy thử lại hoặc dùng email và mật khẩu."


class GoogleAuthenticationNotConfiguredError(AppException):
    status_code = 503
    code = "GOOGLE_AUTH_UNAVAILABLE"
    user_message = "Đăng nhập bằng Google đang tạm không khả dụng."

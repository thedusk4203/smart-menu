# Base application exceptions. Domain/use-case layers raise these (or
# module-specific subclasses) without importing FastAPI. The presentation
# layer (main.py) maps them to HTTP responses via a single exception handler.
from __future__ import annotations

from typing import Any


class AppException(Exception):
    """Base class for all application exceptions. status_code is the HTTP
    status the presentation layer should map this to."""
    status_code: int = 400
    code: str = "APP_ERROR"
    user_message: str = "Không thể hoàn tất yêu cầu. Vui lòng thử lại."

    def __init__(
        self,
        detail: str,
        *,
        code: str | None = None,
        user_message: str | None = None,
        details: dict[str, Any] | None = None,
        fields: dict[str, str] | None = None,
    ) -> None:
        self.detail = detail
        self.code = code or self.code
        self.user_message = user_message or self.user_message
        self.details = details or {}
        self.fields = fields or {}
        super().__init__(detail)

    def response_content(self) -> dict[str, Any]:
        """Return the additive error envelope while preserving legacy detail."""
        error: dict[str, Any] = {
            "code": self.code,
            "message": self.user_message,
            "details": self.details,
        }
        if self.fields:
            error["fields"] = self.fields
        return {"detail": self.detail, "error": error}


class NotFoundError(AppException):
    status_code = 404
    code = "RESOURCE_NOT_FOUND"
    user_message = "Không tìm thấy dữ liệu được yêu cầu."


class ConflictError(AppException):
    status_code = 409
    code = "RESOURCE_CONFLICT"
    user_message = "Dữ liệu đã thay đổi hoặc đang được sử dụng. Hãy tải lại rồi thử lại."


class ValidationAppError(AppException):
    status_code = 422
    code = "VALIDATION_FAILED"
    user_message = "Một số thông tin chưa hợp lệ. Hãy kiểm tra rồi thử lại."


class AuthenticationError(AppException):
    status_code = 401
    code = "AUTH_SESSION_EXPIRED"
    user_message = "Phiên đăng nhập đã hết hạn. Hãy đăng nhập lại để tiếp tục."


class AuthorizationError(AppException):
    status_code = 403
    code = "AUTH_FORBIDDEN"
    user_message = "Bạn không có quyền thực hiện thao tác này."


class GoneError(AppException):
    status_code = 410
    code = "RESOURCE_GONE"
    user_message = "Nội dung này không còn khả dụng."

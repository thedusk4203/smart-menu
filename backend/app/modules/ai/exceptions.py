from __future__ import annotations

from app.core.exceptions import AppException, ValidationAppError


class AIUnavailableError(AppException):
    status_code = 503
    code = "AI_UNAVAILABLE"
    user_message = "Menuto đang tạm gián đoạn. Hãy thử lại sau."


class AIResponseValidationError(ValidationAppError):
    code = "AI_RESPONSE_INVALID"
    user_message = "Menuto chưa tạo được câu trả lời phù hợp. Hãy thử lại."

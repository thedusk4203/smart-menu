from __future__ import annotations

from app.core.exceptions import AppException, ValidationAppError


class AIUnavailableError(AppException):
    status_code = 503


class AIResponseValidationError(ValidationAppError):
    pass

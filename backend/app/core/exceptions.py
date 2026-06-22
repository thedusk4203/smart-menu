# File: backend/app/core/exceptions.py
# Base application exceptions. Domain/use-case layers raise these (or
# module-specific subclasses) without importing FastAPI. The presentation
# layer (main.py) maps them to HTTP responses via a single exception handler.
from __future__ import annotations


class AppException(Exception):
    """Base class for all application exceptions. status_code is the HTTP
    status the presentation layer should map this to."""
    status_code: int = 400

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)


class NotFoundError(AppException):
    status_code = 404


class ConflictError(AppException):
    status_code = 409


class ValidationAppError(AppException):
    status_code = 422

# File: backend/app/modules/identity/schemas.py
# Pydantic request/response DTOs (presentation layer).
from __future__ import annotations

from pydantic import BaseModel, EmailStr

from app.shared.enums import UserRole


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: UserRole = UserRole.USER
    full_name: str | None = None  # forwarded to profiles when creating the empty profile


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    password: str | None = None
    role: UserRole | None = None
    is_active: bool | None = None


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: UserRole
    is_active: bool

    class Config:
        from_attributes = True

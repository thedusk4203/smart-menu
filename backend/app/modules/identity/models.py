# SQLModel ORM model (infrastructure layer) — maps to the `users` table
# created by data/init_db.sql. Not imported by domain.py / use_cases.py.
from __future__ import annotations

from sqlalchemy import Column
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel

from app.shared.enums import UserRole


class UserModel(SQLModel, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    email: str
    hashed_password: str
    role: UserRole = Field(
        sa_column=Column(SAEnum(UserRole, name="user_role", values_callable=lambda obj: [e.value for e in obj], create_type=False), nullable=False)
    )
    is_active: bool = True

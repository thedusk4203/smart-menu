# File: backend/app/modules/identity/repository.py
# SQLModel implementation of UserRepositoryPort (infrastructure layer).
from __future__ import annotations

from sqlmodel import Session, select

from app.modules.identity.domain import UserEntity
from app.modules.identity.models import UserModel
from app.modules.identity.ports import UserRepositoryPort


def _to_entity(row: UserModel) -> UserEntity:
    return UserEntity(
        id=row.id, email=row.email, hashed_password=row.hashed_password,
        role=row.role, is_active=row.is_active,
    )


class SqlUserRepository(UserRepositoryPort):
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_all(self, limit: int, offset: int) -> list[UserEntity]:
        rows = self._session.exec(
            select(UserModel).order_by(UserModel.id).limit(limit).offset(offset)
        ).all()
        return [_to_entity(r) for r in rows]

    def get_by_id(self, user_id: int) -> UserEntity | None:
        row = self._session.get(UserModel, user_id)
        return _to_entity(row) if row else None

    def get_by_email(self, email: str) -> UserEntity | None:
        row = self._session.exec(select(UserModel).where(UserModel.email == email)).first()
        return _to_entity(row) if row else None

    def save(self, user: UserEntity) -> UserEntity:
        if user.id is None:
            row = UserModel(email=user.email, hashed_password=user.hashed_password,
                             role=user.role, is_active=user.is_active)
        else:
            row = self._session.get(UserModel, user.id)
            row.email = user.email
            row.hashed_password = user.hashed_password
            row.role = user.role
            row.is_active = user.is_active
        self._session.add(row)
        self._session.commit()
        self._session.refresh(row)
        return _to_entity(row)

    def delete(self, user_id: int) -> None:
        row = self._session.get(UserModel, user_id)
        if row:
            self._session.delete(row)
            self._session.commit()

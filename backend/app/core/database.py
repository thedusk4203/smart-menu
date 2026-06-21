# File: backend/app/core/database.py
# Database engine and session factory.
#
# NOTE: schema is owned by Alembic migrations / data/init_db.sql (single
# source of truth) — do NOT call SQLModel.metadata.create_all() here.
from __future__ import annotations

from collections.abc import Generator

from sqlmodel import Session, create_engine

from app.core.config import settings

engine = create_engine(settings.database_url, echo=False, pool_pre_ping=True)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session

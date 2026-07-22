from __future__ import annotations

from collections.abc import Generator

from sqlmodel import Session, create_engine

from app.core.config import settings

engine = create_engine(settings.database_url, echo=False, pool_pre_ping=True)
ai_context_engine = create_engine(
    settings.ai_context_database_url or settings.database_url,
    echo=False,
    pool_pre_ping=True,
)
ai_state_engine = create_engine(
    settings.ai_state_database_url or settings.database_url,
    echo=False,
    pool_pre_ping=True,
)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


def get_ai_context_session() -> Generator[Session, None, None]:
    with Session(ai_context_engine) as session:
        yield session


def get_ai_state_session() -> Generator[Session, None, None]:
    with Session(ai_state_engine) as session:
        yield session

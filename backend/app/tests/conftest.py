# File: backend/app/tests/conftest.py
# Fixtures dùng chung cho test TÍCH HỢP cần Postgres đã seed (data/init_db.sql).
# Các test pure-unit (dùng fake/factory) không phụ thuộc fixture này.
from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlmodel import Session

from app.core.database import engine


@pytest.fixture(scope="session")
def db_session():
    """Session gắn với Postgres đang chạy.

    Nếu DB không kết nối được (máy dev không bật Docker) thì SKIP thay vì fail —
    để các test không cần DB vẫn chạy bình thường. Trong CI/môi trường đã seed,
    fixture trả session thật và các invariant dữ liệu chạy đầy đủ.
    """
    try:
        session = Session(engine)
        session.execute(text("SELECT 1"))
    except Exception as exc:  # pragma: no cover - phụ thuộc môi trường
        pytest.skip(f"Bỏ qua test dữ liệu: không kết nối được Postgres ({exc}).")
    try:
        yield session
    finally:
        session.close()

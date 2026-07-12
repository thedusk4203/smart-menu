from __future__ import annotations

import asyncio

import pytest

from app import main


@pytest.mark.asyncio
async def test_lifespan_starts_conversation_retention_cleanup(monkeypatch):
    called = asyncio.Event()

    def purge() -> int:
        called.set()
        return 0

    monkeypatch.setattr(main, "_purge_expired_conversations", purge)

    async with main.lifespan(main.app):
        await asyncio.wait_for(called.wait(), timeout=1)

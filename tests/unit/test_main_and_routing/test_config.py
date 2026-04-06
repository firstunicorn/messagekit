"""Tests for configuration builders and factories."""

import pytest

from messaging.infrastructure.persistence.session import create_session_factory


@pytest.mark.asyncio
async def test_create_session_factory_creates_async_engine() -> None:
    """Session helper should return an engine and a session factory."""
    engine, factory = create_session_factory(
        "postgresql+asyncpg://postgres:postgres@localhost:5432/eventing"
    )

    assert factory.kw["expire_on_commit"] is False
    await engine.dispose()

"""Async engine and session-factory helpers for eventing persistence."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from sqlalchemy_async_session_factory.engine import create_async_engine_with_pool
from sqlalchemy_async_session_factory.session import create_async_session_maker


def create_session_factory(
    database_url: str,
) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    """Create an async SQLAlchemy engine and session factory via toolkit helpers."""
    engine = create_async_engine_with_pool(database_url)
    factory = create_async_session_maker(engine, expire_on_commit=False)
    return engine, factory

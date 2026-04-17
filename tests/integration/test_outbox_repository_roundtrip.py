"""Integration tests for the eventing outbox repository."""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from messaging.core.contracts import BaseEvent
from messaging.infrastructure.outbox.outbox_repository import SqlAlchemyOutboxRepository
from messaging.infrastructure.persistence.orm_models.outbox_orm import OutboxEventRecord


class ExampleEvent(BaseEvent):  # pylint: disable=too-many-ancestors
    """Concrete integration-test event."""

    event_type: str = "gamification.xp.awarded"
    aggregate_id: str = "user-123"
    source: str = "gamification-service"
    xp_delta: int


pytestmark = pytest.mark.asyncio


async def test_repository_marks_events_published(
    sqlite_session_factory: tuple[object, async_sessionmaker[AsyncSession]],
) -> None:
    """Marking an outbox event as published should update the stored record."""
    _, session_factory = sqlite_session_factory
    repository = SqlAlchemyOutboxRepository(session_factory)
    event = ExampleEvent(xp_delta=30)

    await repository.add_event(event)
    await repository.mark_published(event.event_id)

    async with session_factory() as session:
        stored = await session.scalar(
            select(OutboxEventRecord).where(OutboxEventRecord.event_id == str(event.event_id))
        )
    assert stored is not None
    assert stored.published is True
    assert stored.published_at is not None

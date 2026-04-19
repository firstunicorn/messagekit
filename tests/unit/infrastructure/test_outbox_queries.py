"""Unit tests for OutboxQueryOperations query generation.

Uses SQLite to verify actual query structure and behavior.

Note: get_unpublished() now returns empty list as Kafka Connect handles publishing.
These tests verify the query operations for legacy compatibility.
"""

from __future__ import annotations

from typing import Any

import pytest

from messagekit.infrastructure.outbox.outbox_queries import OutboxQueryOperations
from messagekit.infrastructure.persistence.orm_models.outbox_orm import OutboxEventRecord
from tests.unit.infrastructure.conftest import ExampleEvent


@pytest.mark.asyncio
async def test_count_unpublished_excludes_failed(
    sqlite_session_factory: tuple[Any, Any],
) -> None:
    """Count should exclude events marked as failed."""
    engine, factory = sqlite_session_factory
    ops = OutboxQueryOperations(factory)

    event = ExampleEvent(xp_delta=10)
    record = OutboxEventRecord(
        event_id=str(event.event_id),
        event_type=event.event_type,
        aggregate_id=event.aggregate_id,
        payload=event.to_message(),
        occurred_at=event.occurred_at,
        failed=True,
    )
    async with factory() as session:
        session.add(record)
        await session.commit()

    assert await ops.count_unpublished() == 0

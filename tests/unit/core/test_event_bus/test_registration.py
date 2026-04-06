"""Tests for event bus handler registration."""

import pytest

from messaging.core.contracts import HandlerRegistration, build_event_bus
from tests.unit.core.test_event_bus.test_fixtures import ExampleEvent, RecordingHandler


@pytest.mark.asyncio
async def test_event_bus_builds_from_handler_registrations() -> None:
    """The facade should reuse the existing registration shape."""
    handler = RecordingHandler()
    event_bus = build_event_bus([HandlerRegistration(ExampleEvent, handler)])
    event = ExampleEvent(xp_delta=15)

    await event_bus.dispatch(event)

    assert handler.seen == [event]

"""Test fixtures and constants for Testcontainers smoke tests."""

from __future__ import annotations

from messaging.core.contracts import BaseEvent

TEST_TOPIC = "gamification.xp.awarded"
TEST_MESSAGE = {
    "eventType": TEST_TOPIC,
    "aggregateId": "user-123",
    "source": "gamification-service",
    "xpDelta": 15,
}


class ExampleEvent(BaseEvent):  # pylint: disable=too-many-ancestors
    """Concrete event used for container-backed smoke coverage."""

    event_type: str = "gamification.xp.awarded"
    aggregate_id: str = "user-123"
    source: str = "gamification-service"
    xp_delta: int

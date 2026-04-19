"""Unit tests for Kafka publisher behavior."""

from __future__ import annotations

from typing import Any, cast

import pytest
from faststream.confluent import KafkaBroker

from messagekit.infrastructure.pubsub import KafkaEventPublisher
from tests.unit.infrastructure.conftest import FakeKafkaBroker, FakePublisher


def test_kafka_publisher_uses_event_type_as_topic() -> None:
    """Publisher should derive Kafka topic names from event type."""
    publisher = KafkaEventPublisher(cast(Any, FakePublisher()))
    topic = publisher._resolve_topic({"eventType": "gamification.xp.awarded"})

    assert topic == "gamification.xp.awarded"


async def _test_publish_helper(broker: KafkaBroker) -> None:
    """Helper that accepts real KafkaBroker type for Mypy validation."""
    publisher = KafkaEventPublisher(broker)
    message = {
        "eventType": "gamification.xp.awarded",
        "aggregateId": "user-123",
        "source": "gamification-service",
    }
    await publisher.publish_to_topic("gamification.xp.awarded", message)


@pytest.mark.asyncio
async def test_kafka_publisher_serializes_string_keys_to_bytes() -> None:
    """Publisher should encode string aggregate keys for FastStream Kafka."""
    broker = FakeKafkaBroker()
    await _test_publish_helper(cast(KafkaBroker, broker))

    assert len(broker.published) == 1
    call = broker.published[0]
    message = cast(dict[str, object], call["message"])
    assert message["eventType"] == "gamification.xp.awarded"
    assert call["topic"] == "gamification.xp.awarded"
    assert call["key"] == b"user-123"

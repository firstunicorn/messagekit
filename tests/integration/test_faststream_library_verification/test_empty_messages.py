"""Test FastStream behavior with empty messages."""

import asyncio
import json
from typing import Any

import pytest
from confluent_kafka import Producer
from faststream.confluent import KafkaBroker


@pytest.mark.integration
@pytest.mark.requires_kafka
class TestEmptyMessageHandling:
    """Test FastStream behavior with empty messages."""

    @pytest.mark.asyncio
    async def test_empty_json_object(self, kafka_container) -> None:
        """Verify handler doesn't crash on empty JSON object."""
        broker = KafkaBroker(
            bootstrap_servers=kafka_container.get_bootstrap_server(),
            graceful_timeout=1.0,
        )

        received_message = None
        handler_crashed = False

        @broker.subscriber("test-empty-json", group_id="empty-group")
        async def handler(message: dict[str, Any]) -> None:
            nonlocal received_message, handler_crashed
            try:
                received_message = message
                _ = message.get("event_id")
            except Exception:
                handler_crashed = True
                raise

        async with broker:
            await broker.start()
            await asyncio.sleep(5)

            producer = Producer({
                "bootstrap.servers": kafka_container.get_bootstrap_server()
            })
            producer.produce("test-empty-json", value=json.dumps({}).encode())
            producer.flush()

            await asyncio.sleep(8)

            assert not handler_crashed
            assert received_message == {}

    @pytest.mark.asyncio
    async def test_empty_bytes(self, kafka_container) -> None:
        """Verify FastStream behavior with empty message payload."""
        broker = KafkaBroker(
            bootstrap_servers=kafka_container.get_bootstrap_server(),
            graceful_timeout=1.0,
        )

        handler_called = False

        @broker.subscriber("test-empty-bytes", group_id="empty-bytes-group")
        async def handler(message: dict[str, Any]) -> None:
            nonlocal handler_called
            handler_called = True

        async with broker:
            await broker.start()
            await asyncio.sleep(5)

            producer = Producer({
                "bootstrap.servers": kafka_container.get_bootstrap_server()
            })
            producer.produce("test-empty-bytes", value=b"")
            producer.flush()

            await asyncio.sleep(8)

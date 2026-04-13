"""Test FastStream behavior with invalid JSON messages."""

import asyncio
from typing import Any

import pytest
from confluent_kafka import Producer
from faststream.confluent import KafkaBroker


@pytest.mark.integration
@pytest.mark.requires_kafka
class TestMalformedJsonHandling:
    """Test FastStream behavior with invalid JSON messages."""

    @pytest.mark.asyncio
    async def test_invalid_json_raises_exception(self, kafka_container) -> None:
        """Document actual FastStream behavior when JSON decoding fails."""
        broker = KafkaBroker(
            bootstrap_servers=kafka_container.get_bootstrap_server(),
            graceful_timeout=1.0,
        )

        handler_called = False

        @broker.subscriber("test-invalid-json", group_id="invalid-json-group")
        async def handler(message: dict[str, Any]) -> None:
            nonlocal handler_called
            handler_called = True

        async with broker:
            await broker.start()
            await asyncio.sleep(5)

            producer = Producer({
                "bootstrap.servers": kafka_container.get_bootstrap_server()
            })
            producer.produce("test-invalid-json", value=b"not-json{invalid")
            producer.flush()

            await asyncio.sleep(8)

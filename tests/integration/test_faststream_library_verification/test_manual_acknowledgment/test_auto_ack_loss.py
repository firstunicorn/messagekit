"""Test auto-ack message loss behavior."""

import asyncio
import json
from typing import Any

import pytest
from confluent_kafka import Producer
from faststream.confluent import KafkaBroker


@pytest.mark.integration
@pytest.mark.requires_kafka
class TestAutoAckMessageLoss:
    """Test auto-ack loses messages on handler failure."""

    @pytest.mark.asyncio
    async def test_auto_ack_loses_message_on_handler_failure(
        self, kafka_container
    ) -> None:
        """Auto-ack (default) commits offset BEFORE handler executes."""
        broker = KafkaBroker(
            bootstrap_servers=kafka_container.get_bootstrap_server(),
            graceful_timeout=1.0,
        )

        processed_messages = []
        handler_call_count = 0

        @broker.subscriber("test-auto-ack", group_id="test-group-auto")
        async def handler(message: dict[str, Any]) -> None:
            nonlocal handler_call_count
            handler_call_count += 1
            if handler_call_count == 1:
                raise RuntimeError("Handler crashed")
            processed_messages.append(message)

        async with broker:
            await broker.start()
            await asyncio.sleep(5)

            producer = Producer({
                "bootstrap.servers": kafka_container.get_bootstrap_server()
            })
            test_msg = {"event_id": "auto-ack-test", "data": "test"}
            producer.produce("test-auto-ack", value=json.dumps(test_msg).encode())
            producer.flush()

            await asyncio.sleep(8)

            assert handler_call_count == 1
            assert len(processed_messages) == 0

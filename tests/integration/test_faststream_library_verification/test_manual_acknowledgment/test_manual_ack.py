"""Test manual ack prevents message loss."""

import asyncio
import json
from typing import Any

import pytest
from confluent_kafka import Producer
from faststream import AckPolicy
from faststream.confluent import KafkaBroker
from faststream.confluent.annotations import KafkaMessage


@pytest.mark.integration
@pytest.mark.requires_kafka
class TestManualAckPreventsLoss:
    """Test manual ack prevents message loss on handler failure."""

    @pytest.mark.asyncio
    async def test_manual_ack_prevents_message_loss(self, kafka_container) -> None:
        """Manual ack delays commit until after successful processing."""
        broker = KafkaBroker(
            bootstrap_servers=kafka_container.get_bootstrap_server(),
            graceful_timeout=1.0,
        )

        processed_messages = []
        handler_call_count = 0

        @broker.subscriber(
            "test-manual-ack",
            group_id="manual-group",
            ack_policy=AckPolicy.MANUAL,
        )
        async def handler(message: dict[str, Any], msg: KafkaMessage) -> None:
            nonlocal handler_call_count
            handler_call_count += 1

            if handler_call_count == 1:
                await msg.nack()
                return

            processed_messages.append(message)
            await msg.ack()

        async with broker:
            await broker.start()
            await asyncio.sleep(5)

            producer = Producer({
                "bootstrap.servers": kafka_container.get_bootstrap_server()
            })
            test_msg = {"event_id": "manual-ack-test", "data": "test"}
            producer.produce("test-manual-ack", value=json.dumps(test_msg).encode())
            producer.flush()

            await asyncio.sleep(10)

            assert handler_call_count >= 2
            assert len(processed_messages) >= 1

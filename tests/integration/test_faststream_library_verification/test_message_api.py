"""Test KafkaMessage and RabbitMessage object methods."""

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
class TestMessageObjectAPI:
    """Test KafkaMessage and RabbitMessage object methods."""

    @pytest.mark.asyncio
    async def test_kafka_message_ack_method(self, kafka_container) -> None:
        """Verify KafkaMessage.ack() method exists and is callable."""
        broker = KafkaBroker(
            bootstrap_servers=kafka_container.get_bootstrap_server(),
            graceful_timeout=1.0,
        )

        message_obj = None

        @broker.subscriber(
            "test-msg-api",
            group_id="msg-api-group",
            ack_policy=AckPolicy.MANUAL,
        )
        async def handler(message: dict[str, Any], msg: KafkaMessage) -> None:
            nonlocal message_obj
            message_obj = msg
            await msg.ack()

        async with broker:
            await broker.start()
            await asyncio.sleep(5)

            producer = Producer({
                "bootstrap.servers": kafka_container.get_bootstrap_server()
            })
            test_msg = {"event_id": "msg-api-test"}
            producer.produce("test-msg-api", value=json.dumps(test_msg).encode())
            producer.flush()

            await asyncio.sleep(8)

            assert message_obj is not None
            assert hasattr(message_obj, "ack")
            assert hasattr(message_obj, "nack")
            assert hasattr(message_obj, "reject")

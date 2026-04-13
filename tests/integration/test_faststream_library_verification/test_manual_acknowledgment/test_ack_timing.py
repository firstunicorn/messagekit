"""Test ack timing and ordering."""

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
class TestAckTiming:
    """Test ack is called only after successful processing."""

    @pytest.mark.asyncio
    async def test_ack_only_after_successful_processing(
        self, kafka_container
    ) -> None:
        """Verify ack() is called only after all processing succeeds."""
        broker = KafkaBroker(
            bootstrap_servers=kafka_container.get_bootstrap_server(),
            graceful_timeout=1.0,
        )

        ack_called_before_processing = False
        processing_completed = False

        @broker.subscriber(
            "test-ack-timing",
            group_id="timing-group",
            ack_policy=AckPolicy.MANUAL,
        )
        async def handler(message: dict[str, Any], msg: KafkaMessage) -> None:
            nonlocal ack_called_before_processing, processing_completed

            processing_completed = False
            await asyncio.sleep(0.1)
            processing_completed = True

            if not processing_completed:
                ack_called_before_processing = True

            await msg.ack()

        async with broker:
            await broker.start()
            await asyncio.sleep(5)

            producer = Producer({
                "bootstrap.servers": kafka_container.get_bootstrap_server()
            })
            test_msg = {"event_id": "timing-test", "data": "test"}
            producer.produce("test-ack-timing", value=json.dumps(test_msg).encode())
            producer.flush()

            await asyncio.sleep(8)

            assert not ack_called_before_processing
            assert processing_completed

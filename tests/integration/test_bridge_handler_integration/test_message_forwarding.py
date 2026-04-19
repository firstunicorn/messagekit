"""Test production bridge handler message forwarding."""

import asyncio
import json
from uuid import uuid4

import aio_pika
import pytest
from aio_pika import ExchangeType
from aio_pika.exceptions import QueueEmpty
from confluent_kafka import Producer

from messagekit.config import settings as app_settings
from messagekit.main._initialization import (
    initialize_bridge_config,
    initialize_brokers_and_publishers,
    register_bridge_handler,
)


@pytest.mark.integration
@pytest.mark.requires_kafka
@pytest.mark.requires_rabbitmq
class TestMessageForwarding:
    """Test actual production bridge handler with real infrastructure."""

    @pytest.mark.asyncio
    async def test_production_handler_forwards_kafka_to_rabbitmq(
        self,
        kafka_container,
        rabbitmq_container,
        sqlite_session_factory,
        monkeypatch,
    ) -> None:
        """Test the ACTUAL production handle_kafka_event subscriber."""
        kafka_bootstrap = kafka_container.get_bootstrap_server()
        rabbitmq_url = (
            f"amqp://{rabbitmq_container.username}:{rabbitmq_container.password}"
            f"@{rabbitmq_container.get_container_host_ip()}"
            f":{rabbitmq_container.get_exposed_port(rabbitmq_container.port)}//"
        )

        monkeypatch.setattr(app_settings, "kafka_bootstrap_servers", kafka_bootstrap)
        monkeypatch.setattr(app_settings, "rabbitmq_url", rabbitmq_url)

        _, async_session_factory = sqlite_session_factory
        monkeypatch.setattr(app_settings, "rabbitmq_exchange", "test-events")

        broker, rabbit_broker, rabbit_publisher = initialize_brokers_and_publishers()
        bridge_config = initialize_bridge_config()

        register_bridge_handler(
            broker, bridge_config, rabbit_publisher, async_session_factory
        )

        async with broker, rabbit_broker:
            await broker.start()
            await rabbit_broker.start()

            connection = await aio_pika.connect_robust(rabbitmq_url)
            channel = await connection.channel()

            exchange = await channel.declare_exchange(
                "test-events", ExchangeType.TOPIC, durable=True
            )
            queue = await channel.declare_queue(f"test-queue-{uuid4()}", auto_delete=True)
            await queue.bind(exchange, routing_key="user.#")

            await asyncio.sleep(5)

            producer = Producer({"bootstrap.servers": kafka_bootstrap})
            event_id = f"prod-test-{uuid4()}"
            test_msg = {
                "event_id": event_id,
                "event_type": "user.created",
                "data": {"user_id": 123},
            }
            producer.produce("events", value=json.dumps(test_msg).encode())
            producer.flush()

            await asyncio.sleep(15)

            try:
                rabbit_msg = await asyncio.wait_for(queue.get(timeout=30), timeout=35)
                received_data = json.loads(rabbit_msg.body.decode())

                assert received_data["event_id"] == event_id
                assert received_data["event_type"] == "user.created"
                assert received_data["data"]["user_id"] == 123

                await rabbit_msg.ack()
            except (TimeoutError, QueueEmpty) as e:
                pytest.fail(f"Message not forwarded to RabbitMQ: {e}")

            await connection.close()

"""Initialization helpers for application infrastructure."""

from typing import Any

from fastapi import FastAPI
from faststream.confluent import KafkaBroker
from faststream.rabbit import RabbitBroker

from messaging.config import settings
from messaging.core.contracts import build_event_bus
from messaging.infrastructure import (
    EventingHealthCheck,
    SqlAlchemyOutboxRepository,
    SqlAlchemyProcessedMessageStore,
    create_kafka_broker,
)
from messaging.infrastructure.pubsub.bridge.config import BridgeConfig
from messaging.infrastructure.pubsub.bridge.consumer import BridgeConsumer
from messaging.infrastructure.pubsub.rabbit.publisher import RabbitEventPublisher
from messaging.infrastructure.pubsub.rabbit_broker_config import create_rabbit_broker


def initialize_brokers_and_publishers() -> tuple[
    KafkaBroker,
    RabbitBroker,
    RabbitEventPublisher,
]:
    """Initialize Kafka and RabbitMQ brokers with publishers.

    Returns:
        Tuple of (kafka_broker, rabbit_broker, rabbit_publisher)
    """
    broker = create_kafka_broker(
        settings,
        enable_rate_limiter=settings.rate_limiter_enabled,
        rate_limit_max_rate=settings.rate_limiter_max_rate,
        rate_limit_time_period=settings.rate_limiter_time_period,
    )

    rabbit_broker = create_rabbit_broker(
        settings,
        enable_rate_limiter=settings.rabbitmq_rate_limiter_enabled,
        rate_limit_max_rate=settings.rabbitmq_rate_limit,
        rate_limit_time_period=settings.rabbitmq_rate_interval,
    )

    rabbit_publisher = RabbitEventPublisher(
        broker=rabbit_broker,
        default_exchange=settings.rabbitmq_exchange,
    )

    return broker, rabbit_broker, rabbit_publisher


def initialize_bridge_consumer(
    rabbit_publisher: RabbitEventPublisher,
    processed_message_store: SqlAlchemyProcessedMessageStore,
) -> tuple[BridgeConfig, BridgeConsumer]:
    """Initialize Kafka-to-RabbitMQ bridge consumer.

    Args:
        rabbit_publisher: RabbitMQ event publisher
        processed_message_store: Store for idempotency tracking

    Returns:
        Tuple of (bridge_config, bridge_consumer)
    """
    bridge_config = BridgeConfig(
        kafka_topic="events",
        rabbitmq_exchange=settings.rabbitmq_exchange,
        routing_key_template="{event_type}",
    )

    bridge_consumer = BridgeConsumer(
        rabbit_publisher=rabbit_publisher,
        processed_message_store=processed_message_store,
        routing_key_template=bridge_config.routing_key_template,
    )

    return bridge_config, bridge_consumer


def register_bridge_handler(
    broker: KafkaBroker,
    bridge_config: BridgeConfig,
    bridge_consumer: BridgeConsumer,
) -> None:
    """Register bridge consumer as Kafka subscriber.

    Args:
        broker: Kafka broker
        bridge_config: Bridge configuration
        bridge_consumer: Bridge consumer instance
    """
    @broker.subscriber(bridge_config.kafka_topic)
    async def handle_kafka_event(message: dict[str, Any]) -> None:
        """Bridge handler: consume from Kafka, forward to RabbitMQ."""
        await bridge_consumer.handle_message(message)


def attach_state_to_app(
    app: FastAPI,
    broker: KafkaBroker,
    rabbit_broker: RabbitBroker,
    rabbit_publisher: RabbitEventPublisher,
    bridge_consumer: BridgeConsumer,
    processed_message_store: SqlAlchemyProcessedMessageStore,
    repository: SqlAlchemyOutboxRepository,
) -> None:
    """Attach all infrastructure instances to FastAPI app state.

    Args:
        app: FastAPI application
        broker: Kafka broker
        rabbit_broker: RabbitMQ broker
        rabbit_publisher: RabbitMQ publisher
        bridge_consumer: Bridge consumer
        processed_message_store: Processed message store
        repository: Outbox repository
    """
    event_bus = build_event_bus([])

    app.state.broker = broker
    app.state.rabbit_broker = rabbit_broker
    app.state.rabbit_publisher = rabbit_publisher
    app.state.bridge_consumer = bridge_consumer
    app.state.processed_message_store = processed_message_store
    app.state.outbox_health_check = EventingHealthCheck(repository, broker)
    app.state.outbox_repository = repository
    app.state.event_bus = event_bus

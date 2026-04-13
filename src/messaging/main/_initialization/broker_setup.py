"""Broker and publisher initialization."""

from faststream.confluent import KafkaBroker
from faststream.rabbit import RabbitBroker

from messaging.config import settings
from messaging.infrastructure import create_kafka_broker
from messaging.infrastructure.pubsub.rabbit.publisher import RabbitEventPublisher
from messaging.infrastructure.pubsub.rabbit_broker_config import create_rabbit_broker


def initialize_brokers_and_publishers() -> (
    tuple[
        KafkaBroker,
        RabbitBroker,
        RabbitEventPublisher,
    ]
):
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

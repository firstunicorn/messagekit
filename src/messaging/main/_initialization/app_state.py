"""FastAPI app state initialization."""

from fastapi import FastAPI
from faststream.confluent import KafkaBroker
from faststream.rabbit import RabbitBroker

from messaging.core.contracts import build_event_bus
from messaging.infrastructure import EventingHealthCheck, SqlAlchemyOutboxRepository
from messaging.infrastructure.pubsub.rabbit.publisher import RabbitEventPublisher


def attach_state_to_app(
    app: FastAPI,
    broker: KafkaBroker,
    rabbit_broker: RabbitBroker,
    rabbit_publisher: RabbitEventPublisher,
    repository: SqlAlchemyOutboxRepository,
) -> None:
    """Attach all infrastructure instances to FastAPI app state.

    Args:
        app: FastAPI application
        broker: Kafka broker
        rabbit_broker: RabbitMQ broker
        rabbit_publisher: RabbitMQ publisher
        repository: Outbox repository
    """
    event_bus = build_event_bus([])

    app.state.broker = broker
    app.state.rabbit_broker = rabbit_broker
    app.state.rabbit_publisher = rabbit_publisher
    app.state.outbox_health_check = EventingHealthCheck(repository, broker)
    app.state.outbox_repository = repository
    app.state.event_bus = event_bus

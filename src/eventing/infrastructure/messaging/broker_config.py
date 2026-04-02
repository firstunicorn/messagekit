"""Factory for the FastStream Kafka broker."""

from faststream.kafka import KafkaBroker

from eventing.config import Settings


def create_kafka_broker(settings: Settings) -> KafkaBroker:
    """Create a Kafka broker configured for idempotent publishing."""
    return KafkaBroker(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        client_id=settings.kafka_client_id,
        enable_idempotence=True,
    )

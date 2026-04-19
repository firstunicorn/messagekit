"""RabbitMQ broker factory with middleware stacking."""

from messagekit.infrastructure.pubsub.rabbit_broker_config.factory import create_rabbit_broker

__all__ = ["create_rabbit_broker"]

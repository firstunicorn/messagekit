"""Kafka-to-RabbitMQ bridge configuration and handler registration."""

from .config import initialize_bridge_config
from .handler_registration import register_bridge_handler

__all__ = ["initialize_bridge_config", "register_bridge_handler"]

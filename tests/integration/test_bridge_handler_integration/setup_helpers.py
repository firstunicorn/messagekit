"""Setup helpers for bridge handler integration tests."""

from typing import Any

from messaging.config import settings as app_settings
from messaging.main._initialization import (
    initialize_bridge_config,
    initialize_brokers_and_publishers,
    register_bridge_handler,
)


def setup_test_containers_config(
    kafka_container: Any,
    rabbitmq_container: Any,
    monkeypatch: Any,
    exchange: str = "test-events",
) -> tuple[str, str]:
    """Configure app settings to use test containers."""
    kafka_bootstrap = kafka_container.get_bootstrap_server()
    rabbitmq_url = (
        f"amqp://{rabbitmq_container.username}:{rabbitmq_container.password}"
        f"@{rabbitmq_container.get_container_host_ip()}"
        f":{rabbitmq_container.get_exposed_port(rabbitmq_container.port)}//"
    )

    monkeypatch.setattr(app_settings, "kafka_bootstrap_servers", kafka_bootstrap)
    monkeypatch.setattr(app_settings, "rabbitmq_url", rabbitmq_url)
    monkeypatch.setattr(app_settings, "rabbitmq_exchange", exchange)

    return kafka_bootstrap, rabbitmq_url


def initialize_production_bridge(session_factory: Any) -> tuple[Any, Any]:
    """Initialize production bridge components."""
    broker, rabbit_broker, rabbit_publisher = initialize_brokers_and_publishers()
    bridge_config = initialize_bridge_config()
    register_bridge_handler(broker, bridge_config, rabbit_publisher, session_factory)
    return broker, rabbit_broker

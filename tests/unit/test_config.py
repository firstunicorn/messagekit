"""Unit tests for application configuration settings."""

from messaging.config import Settings


def test_rabbitmq_settings_defaults() -> None:
    """RabbitMQ settings have correct defaults."""
    settings = Settings()
    assert settings.rabbitmq_url == "amqp://guest:guest@localhost:5672//"
    assert settings.rabbitmq_exchange == "events"
    assert settings.rabbitmq_exchange_type == "topic"
    assert settings.rabbitmq_publisher_confirms is True
    assert settings.rabbitmq_rate_limiter_enabled is False

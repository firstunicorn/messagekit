"""RabbitMQ-specific configuration settings."""

from pydantic import BaseModel, Field


class RabbitMQSettings(BaseModel):
    """RabbitMQ broker configuration settings."""

    rabbitmq_url: str = Field(
        default="amqp://guest:guest@localhost:5672//",
        description="RabbitMQ connection URL (AMQP protocol)",
    )
    rabbitmq_exchange: str = Field(
        default="events",
        description="Default RabbitMQ exchange for publishing events",
    )
    rabbitmq_exchange_type: str = Field(
        default="topic",
        description="RabbitMQ exchange type (topic, direct, fanout, headers)",
    )
    rabbitmq_exchange_durable: bool = Field(
        default=True,
        description="Whether the RabbitMQ exchange should be durable",
    )
    rabbitmq_publisher_confirms: bool = Field(
        default=True,
        description="Enable RabbitMQ publisher confirms for reliability",
    )
    rabbitmq_rate_limit: int = Field(
        default=500,
        description="Max RabbitMQ messages per interval",
    )
    rabbitmq_rate_interval: float = Field(
        default=60.0,
        description="RabbitMQ rate window seconds",
    )
    rabbitmq_rate_limiter_enabled: bool = Field(
        default=False,
        description="Enable rate limiting middleware for RabbitMQ consumption",
    )

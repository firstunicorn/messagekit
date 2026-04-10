"""Integration tests for main application lifespan.

Note: This test requires a running RabbitMQ instance and has known issues
with testcontainers on Windows. It can be skipped with `-m "not requires_rabbitmq"`.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
@pytest.mark.requires_rabbitmq
async def test_lifespan_initializes_rabbit_broker(
    async_client_with_kafka: AsyncClient,
) -> None:
    """Application lifespan creates and starts RabbitMQ broker."""
    # The async_client_with_kafka fixture already initializes the full app lifespan
    # including both Kafka and RabbitMQ brokers. We just need to verify state.
    app = async_client_with_kafka._transport._app  # type: ignore[attr-defined]

    assert hasattr(app.state, "rabbit_broker")
    assert hasattr(app.state, "rabbit_publisher")
    assert app.state.rabbit_broker is not None
    assert app.state.rabbit_publisher is not None
    assert hasattr(app.state, "kafka_broker")
    assert app.state.kafka_broker is not None


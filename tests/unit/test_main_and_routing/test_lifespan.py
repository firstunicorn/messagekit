"""Tests for application lifespan behavior."""

from types import SimpleNamespace

import pytest
from fastapi import FastAPI

from messagekit.main.lifespan import lifespan


@pytest.mark.asyncio
async def test_lifespan_initializes_and_cleans_up_infrastructure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Lifespan should initialize infrastructure and clean up on shutdown."""
    # Skip broker connection using existing environment variable
    monkeypatch.setenv("TESTING_SKIP_BROKER", "true")

    # Patch settings to use in-memory database
    monkeypatch.setattr(
        "messagekit.config.settings",
        SimpleNamespace(
            database_url="sqlite:///:memory:",  # In-memory SQLite for testing
            rate_limiter_enabled=False,
            rate_limiter_max_rate=100,
            rate_limiter_time_period=1.0,
            rabbitmq_rate_limiter_enabled=False,
            rabbitmq_rate_limit=500,
            rabbitmq_rate_interval=60.0,
            rabbitmq_exchange="events",
        ),
    )

    app = FastAPI()

    async with lifespan(app):
        # Verify key state was attached
        assert hasattr(app.state, "session_factory")
        assert hasattr(app.state, "outbox_repository")
        assert hasattr(app.state, "outbox_health_check")
        assert hasattr(app.state, "event_bus")
        assert hasattr(app.state, "rabbit_publisher")
        assert hasattr(app.state, "broker")
        assert hasattr(app.state, "rabbit_broker")

    # Test passed - cleanup logic was executed without errors

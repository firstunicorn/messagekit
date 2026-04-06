"""Tests for application lifespan behavior."""

from types import SimpleNamespace

import pytest
from fastapi import FastAPI

from messaging.main import lifespan
from tests.unit.test_main_and_routing.test_fixtures import FakeBroker, FakeEngine


@pytest.mark.asyncio
async def test_lifespan_initializes_and_cleans_up_infrastructure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Lifespan should initialize infrastructure and clean up on shutdown."""
    engine = FakeEngine()
    broker = FakeBroker()
    monkeypatch.setattr(
        "messaging.main.settings",
        SimpleNamespace(database_url="db"),
    )
    monkeypatch.setattr("messaging.main.create_session_factory", lambda _: (engine, object()))
    monkeypatch.setattr("messaging.main.create_kafka_broker", lambda _: broker)
    monkeypatch.setattr(
        "messaging.main.SqlAlchemyOutboxRepository", lambda session_factory: "repo"
    )
    monkeypatch.setattr("messaging.main.build_event_bus", lambda _: "event_bus")
    monkeypatch.setattr(
        "messaging.main.EventingHealthCheck", lambda repository, broker: "health"
    )
    app = FastAPI()

    async with lifespan(app):
        assert app.state.outbox_repository == "repo"
        assert app.state.outbox_health_check == "health"
        assert app.state.event_bus == "event_bus"
        assert broker.connected is True
        assert broker.started is True

    assert broker.closed is True
    assert engine.disposed is True

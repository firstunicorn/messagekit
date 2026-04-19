"""Application lifecycle manager.

This module provides the lifespan manager that wires up the complete event infrastructure.
Outbox publishing is delegated to Kafka Connect (Debezium).
"""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from messagekit.config import settings
from messagekit.infrastructure import SqlAlchemyOutboxRepository, create_session_factory
from messagekit.main._initialization import (
    attach_state_to_app,
    initialize_bridge_config,
    initialize_brokers_and_publishers,
    register_bridge_handler,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialize and tear down infrastructure for the service.

    This lifespan manager wires up the complete event infrastructure:
    1. Database session factory for persistence
    2. EventBus for domain event dispatch (handlers registered per-route as needed)
    3. Kafka broker for external messaging
    4. RabbitMQ broker for event distribution

    Outbox publishing is handled by Kafka Connect (Debezium CDC).

    The EventBus enables decoupled domain event dispatch within the service.
    Handlers can register for specific event types using:
        app.state.session_factory = session_factory
        @app.state.event_bus.subscriber(EventType)
        async def handle_event(event: EventType): ...

    Args:
        app: FastAPI application instance

    Yields:
        None: Control flow during application runtime
    """
    if hasattr(app.state, "session_factory"):
        session_factory = app.state.session_factory
        engine = None
    else:
        engine, session_factory = create_session_factory(settings.database_url)
        app.state.session_factory = session_factory

    repository = SqlAlchemyOutboxRepository(session_factory)

    broker, rabbit_broker, rabbit_publisher = initialize_brokers_and_publishers()
    bridge_config = initialize_bridge_config()
    register_bridge_handler(broker, bridge_config, rabbit_publisher, session_factory)
    attach_state_to_app(
        app,
        broker,
        rabbit_broker,
        rabbit_publisher,
        repository,
    )

    skip_broker = os.getenv("TESTING_SKIP_BROKER") == "true"

    try:
        if not skip_broker:
            await broker.connect()
            await broker.start()
            await rabbit_broker.connect()
            await rabbit_broker.start()
        yield
    finally:
        if not skip_broker:
            await broker.stop()
            await rabbit_broker.stop()
        if engine is not None:
            await engine.dispose()

"""FastAPI application entrypoint for the eventing service.

This module provides the `create_app` factory and application lifecycle manager.
It wires together the database session, Kafka broker, and outbox repository.

See Also
--------
- messaging.presentation.router : API routes registered with the application
- messaging.config.Settings : Configuration used during initialization
"""

from messaging.main.app import app
from messaging.main.app_factory import create_app
from messaging.main.lifespan import lifespan

__all__ = ["app", "create_app", "lifespan"]

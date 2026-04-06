"""Tests for app factory and route registration."""

from fastapi.routing import APIRoute

from messaging.main import create_app


def test_create_app_sets_title_and_registers_routes() -> None:
    """App factory should keep service metadata and include health routes."""
    app = create_app()
    paths = {route.path for route in app.routes if isinstance(route, APIRoute)}

    assert app.title == "eventing"
    assert "/api/v1/health" in paths
    assert "/api/v1/health/outbox" in paths

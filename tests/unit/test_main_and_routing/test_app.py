"""Tests for app factory and route registration."""

from messagekit.main import create_app


def test_create_app_sets_title_and_registers_routes() -> None:
    """App factory should keep service metadata and include health routes."""
    app = create_app()
    paths = {route.path for route in app.routes if hasattr(route, "path") and route.path}
    for route in app.routes:
        if hasattr(route, "effective_route_contexts"):
            paths.update(ctx.path for ctx in route.effective_route_contexts())

    assert app.title == "eventing"
    assert "/api/v1/health" in paths
    assert "/api/v1/health/outbox" in paths

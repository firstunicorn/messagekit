"""Tests for event bus dispatch backends."""

import pytest

from messagekit.core.contracts import BaseEvent, SequentialDispatchBackend
from messagekit.core.contracts.event_bus import DispatchBackend, EventBus
from tests.unit.core.test_event_bus.test_fixtures import ExampleEvent, ReversingBackend


@pytest.mark.asyncio
async def test_event_bus_allows_custom_backends() -> None:
    """Backends should control handler execution order."""
    seen: list[str] = []
    backend = ReversingBackend()
    event_bus = EventBus(backend=backend)

    @event_bus.subscriber(ExampleEvent, handler_name="first")
    async def first(event: BaseEvent) -> None:
        _ = event
        seen.append("first")

    @event_bus.subscriber(ExampleEvent, handler_name="second")
    async def second(event: BaseEvent) -> None:
        _ = event
        seen.append("second")

    await event_bus.dispatch(ExampleEvent(xp_delta=40))

    assert backend.seen_handlers == [["first", "second"]]
    assert seen == ["second", "first"]


def test_sequential_dispatch_backend_has_stable_name() -> None:
    """The default backend should expose a predictable identifier."""
    backend: DispatchBackend = SequentialDispatchBackend()
    assert SequentialDispatchBackend().name == "sequential"
    assert backend.name == "sequential"

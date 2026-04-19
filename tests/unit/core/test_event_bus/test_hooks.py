"""Tests for event bus dispatch hooks."""

import pytest

from messagekit.core.contracts import BaseEvent, DispatchHooks, DispatchSettings
from messagekit.core.contracts.event_bus import EventBus
from tests.unit.core.test_event_bus.test_fixtures import ExampleEvent


@pytest.mark.asyncio
async def test_event_bus_exposes_global_success_and_failure_hooks() -> None:
    """Lifecycle hooks should expose handler-level dispatch outcomes."""
    traces: list[tuple[str, str | None]] = []
    event_bus = EventBus(
        hooks=DispatchHooks(
            on_dispatch=lambda trace: traces.append((trace.stage, trace.handler_name)),
            on_success=lambda trace: traces.append((trace.stage, trace.handler_name)),
            on_failure=lambda trace: traces.append((trace.stage, trace.handler_name)),
        )
    )

    @event_bus.subscriber(ExampleEvent, handler_name="ok-handler")
    async def succeed(event: BaseEvent) -> None:
        _ = event

    @event_bus.subscriber(ExampleEvent, handler_name="boom-handler")
    async def fail(event: BaseEvent) -> None:
        _ = event
        msg = "boom"
        raise RuntimeError(msg)

    with pytest.raises(RuntimeError, match="boom"):
        await event_bus.dispatch(ExampleEvent(xp_delta=30))

    assert traces == [
        ("dispatch", "ok-handler"),
        ("success", "ok-handler"),
        ("dispatch", "boom-handler"),
        ("failure", "boom-handler"),
    ]


@pytest.mark.asyncio
async def test_event_bus_debug_and_disable_hooks_are_explicit() -> None:
    """Disabled dispatch should skip handlers and still emit debug traces."""
    disabled: list[str] = []
    debug: list[str] = []
    event_bus = EventBus(
        hooks=DispatchHooks(
            on_disabled=lambda trace: disabled.append(trace.stage),
            on_debug=lambda trace: debug.append(trace.stage),
        ),
        settings=DispatchSettings(enabled=False, debug=True),
    )

    await event_bus.dispatch(ExampleEvent(xp_delta=35))

    assert disabled == ["disabled"]
    assert debug == ["disabled"]

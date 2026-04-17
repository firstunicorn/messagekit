"""Shared test fixtures for event bus tests."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from messaging.core.contracts import BaseEvent
from messaging.core.contracts.event_bus import RegisteredHandler
from python_domain_events import IDomainEventHandler


class ExampleEvent(BaseEvent):
    """Concrete event for event-bus tests."""

    event_type: str = "gamification.xp.awarded"
    aggregate_id: str = "user-123"
    source: str = "gamification-service"
    xp_delta: int


class RecordingHandler(IDomainEventHandler[BaseEvent]):
    """Collect dispatched events."""

    def __init__(self) -> None:
        self.seen: list[BaseEvent] = []

    async def handle(self, event: BaseEvent) -> None:
        self.seen.append(event)


class ReversingBackend:
    """Custom backend used to prove backend abstraction works."""

    name = "reversing"

    def __init__(self) -> None:
        self.seen_handlers: list[list[str]] = []

    async def invoke(
        self,
        event: BaseEvent,
        handlers: list[RegisteredHandler],
        invoke_one: Callable[[RegisteredHandler], Awaitable[None]],
    ) -> None:
        _ = event
        self.seen_handlers.append([handler.name for handler in handlers])
        for handler in reversed(handlers):
            await invoke_one(handler)

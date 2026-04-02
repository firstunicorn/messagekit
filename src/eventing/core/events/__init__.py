"""Eventing core event contracts and helpers."""

from eventing.core.events.base_event import BaseEvent
from eventing.core.events.dispatch_hooks import DispatchHooks, DispatchSettings, DispatchTrace
from eventing.core.events.dispatcher_setup import (
    HandlerRegistration,
    build_dispatcher,
    build_event_bus,
)
from eventing.core.events.event_envelope import EventEnvelopeFormatter
from eventing.core.events.event_bus import DispatchBackend, EventBus, SequentialDispatchBackend
from eventing.core.events.event_registry import EventRegistry, UnknownEventTypeError

__all__ = [
    "BaseEvent",
    "DispatchBackend",
    "DispatchHooks",
    "DispatchSettings",
    "DispatchTrace",
    "EventBus",
    "EventEnvelopeFormatter",
    "EventRegistry",
    "HandlerRegistration",
    "SequentialDispatchBackend",
    "UnknownEventTypeError",
    "build_dispatcher",
    "build_event_bus",
]

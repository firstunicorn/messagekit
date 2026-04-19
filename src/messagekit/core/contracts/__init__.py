"""Event contracts, registry, and dispatch patterns.

This package defines the core eventing contracts:

**Event Definitions**
  - BaseEvent : Canonical event schema with CloudEvents fields
  - EventRegistry : Type registry for event deserialization

**Dispatch Patterns**
  - EventBus : High-level decorator-style API with hooks
  - build_dispatcher : Mediator-based command/event routing
  - build_event_bus : Factory for pre-configured event bus

**Envelope Formatting**
  - EventEnvelopeFormatter : CloudEvents 1.0 wrapper for Kafka

See Also
--------
- messaging.core.contracts.bus : Event bus facade and dispatch backends
- messaging.infrastructure.outbox : Transactional outbox handler
"""

from messagekit.core.contracts.base_event import BaseEvent
from messagekit.core.contracts.bus import DispatchBackend, EventBus, SequentialDispatchBackend
from messagekit.core.contracts.dispatch_hooks import DispatchHooks, DispatchSettings, DispatchTrace
from messagekit.core.contracts.dispatcher_setup import (
    HandlerRegistration,
    build_dispatcher,
    build_event_bus,
)
from messagekit.core.contracts.event_envelope import EventEnvelopeFormatter
from messagekit.core.contracts.event_registry import EventRegistry, UnknownEventTypeError

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

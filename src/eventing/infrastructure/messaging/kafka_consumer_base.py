"""Idempotent consumer base with simple in-memory deduplication."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class IdempotentConsumerBase(ABC):
    """Skip duplicate events by event identifier within the process lifetime."""

    def __init__(self) -> None:
        self._processed_ids: set[str] = set()

    async def consume(self, message: dict[str, Any]) -> bool:
        """Process a message once, returning whether work was performed."""
        event_id = str(message.get("eventId") or message.get("event_id"))
        if not event_id or event_id in self._processed_ids:
            return False
        await self.handle_event(message)
        self._processed_ids.add(event_id)
        return True

    @abstractmethod
    async def handle_event(self, message: dict[str, Any]) -> None:
        """Handle one deserialized event payload."""

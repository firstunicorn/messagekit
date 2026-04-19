"""Helper functions for outbox CRUD operations."""

from messagekit.core.contracts import BaseEvent
from messagekit.infrastructure.persistence.orm_models.outbox_orm import OutboxEventRecord
from python_outbox_core import IOutboxEvent


def to_record(event: IOutboxEvent) -> OutboxEventRecord:
    """Convert domain event to ORM record.

    Args:
        event: The outbox event to convert

    Returns:
        ORM record ready for persistence
    """
    payload = event.to_message()
    base_event = BaseEvent.model_validate(payload)
    return OutboxEventRecord(
        event_id=str(event.event_id),
        event_type=event.event_type,
        aggregate_id=event.aggregate_id,
        payload=payload,
        occurred_at=base_event.occurred_at,
    )

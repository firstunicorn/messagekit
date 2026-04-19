"""Transactional outbox pattern implementation.

The outbox pattern ensures reliable event publishing by storing events
in the application database within the same transaction as business data.
Publishing to Kafka is delegated to Kafka Connect (Debezium CDC).

**Core components**
  - OutboxEventHandler : Store events in outbox during transaction
  - SqlAlchemyOutboxRepository : CRUD operations on outbox table

**Guarantees**
  - At-least-once delivery (events never lost, may be duplicated)
  - Ordered publication per aggregate (events publish in insert order)
  - Survives app crashes (unpublished events persist in database)

**Usage pattern**
  1. Register OutboxEventHandler as domain event listener
  2. Emit domain events in application transaction
  3. Events automatically save to outbox_events table
  4. Kafka Connect (Debezium) streams changes from outbox table to Kafka

See Also
--------
- messaging.core : Domain event definitions
- messaging.infrastructure.messaging : KafkaEventPublisher
- messaging.infrastructure.persistence : OutboxEventRecord ORM model
"""

from messagekit.infrastructure.outbox.outbox_event_handler import OutboxEventHandler
from messagekit.infrastructure.outbox.outbox_repository import SqlAlchemyOutboxRepository

__all__ = [
    "OutboxEventHandler",
    "SqlAlchemyOutboxRepository",
]

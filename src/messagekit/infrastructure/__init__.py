"""Infrastructure implementations for event persistence and messaging.

This layer provides concrete implementations of technical concerns:

**Transactional Outbox**
  - OutboxEventHandler : Persist events in application transaction
  - SqlAlchemyOutboxRepository : Outbox table operations

**Kafka Integration**
  - KafkaEventPublisher : Publish events to Kafka topics
  - IdempotentConsumerBase : Replay-safe consumer with deduplication

**Persistence**
  - OutboxEventRecord, ProcessedMessageRecord : SQLAlchemy ORM models
  - SqlAlchemyProcessedMessageStore : Consumer idempotency tracking
  - create_session_factory : Async session configuration

**Health Checks**
  - EventingHealthCheck : Outbox staleness monitoring

See Also
--------
- messaging.core : Domain-agnostic event contracts
- messaging.infrastructure.outbox : Outbox pattern implementation
- messaging.infrastructure.messaging : Kafka adapters
- messaging.infrastructure.persistence : Database models and stores
"""

from messagekit.infrastructure.health import EventingHealthCheck
from messagekit.infrastructure.outbox import OutboxEventHandler, SqlAlchemyOutboxRepository
from messagekit.infrastructure.persistence import (
    OutboxEventRecord,
    ProcessedMessageRecord,
    SqlAlchemyProcessedMessageStore,
    create_session_factory,
)
from messagekit.infrastructure.pubsub import (
    IdempotentConsumerBase,
    IProcessedMessageStore,
    KafkaEventPublisher,
    create_kafka_broker,
)

__all__ = [
    "EventingHealthCheck",
    "IProcessedMessageStore",
    "IdempotentConsumerBase",
    "KafkaEventPublisher",
    "OutboxEventHandler",
    "OutboxEventRecord",
    "ProcessedMessageRecord",
    "SqlAlchemyOutboxRepository",
    "SqlAlchemyProcessedMessageStore",
    "create_kafka_broker",
    "create_session_factory",
]

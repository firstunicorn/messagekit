"""Kafka messaging adapters and consumer patterns.

This module provides Kafka integration with built-in reliability patterns:

**Publishing**
  - KafkaEventPublisher : Publish CloudEvents to Kafka topics
  - Resolves topic from event metadata
  - Handles serialization and error recovery

**Consuming**
  - IdempotentConsumerBase : Base class for replay-safe consumers
  - Automatic deduplication using ProcessedMessageStore
  - Prevents duplicate processing on Kafka redelivery

**Configuration**
  - create_kafka_broker : FastStream Kafka broker factory
  - IProcessedMessageStore : Interface for idempotency stores

**Dead Letter Queue**
  - DLQ handling delegated to native RabbitMQ DLX and Kafka Connect DLQ SMT
  - DB bookkeeping maintained via dlq_bookkeeper consumer
  - update_db_flag_for_dlq_event : Update database flags for DLQ events

See Also
--------
- messaging.infrastructure.persistence : Idempotency store implementations
- messaging.infrastructure.pubsub.dlq_bookkeeper : DLQ database updater
"""

from messagekit.infrastructure.pubsub.broker_config import create_kafka_broker
from messagekit.infrastructure.pubsub.consumer_base.kafka_consumer_base import (
    IdempotentConsumerBase,
)
from messagekit.infrastructure.pubsub.dlq_bookkeeper import (
    extract_error_reason,
    extract_event_id,
    update_db_flag_for_dlq_event,
)
from messagekit.infrastructure.pubsub.kafka_publisher import KafkaEventPublisher
from messagekit.infrastructure.pubsub.processed_message_store import IProcessedMessageStore

__all__ = [
    "IProcessedMessageStore",
    "IdempotentConsumerBase",
    "KafkaEventPublisher",
    "create_kafka_broker",
    "extract_error_reason",
    "extract_event_id",
    "update_db_flag_for_dlq_event",
]

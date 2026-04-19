"""Consumer base sub-package.

Re-exports the public API of the consumer base module for convenience.
"""

from messagekit.infrastructure.pubsub.consumer_base.consumer_consume import consume_event
from messagekit.infrastructure.pubsub.consumer_base.consumer_helpers import extract_event_id
from messagekit.infrastructure.pubsub.consumer_base.consumer_validators import (
    validate_consumer_name,
)
from messagekit.infrastructure.pubsub.consumer_base.kafka_consumer_base import (
    IdempotentConsumerBase,
)

__all__ = [
    "IdempotentConsumerBase",
    "consume_event",
    "extract_event_id",
    "validate_consumer_name",
]

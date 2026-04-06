"""DLQ bookkeeper consumer for database failure tracking.

This module provides a lightweight FastStream consumer that listens to native
DLQ topics (RabbitMQ DLX and Kafka Connect DLQ) and updates the `outbox_event_record`
table to mark events as failed, maintaining operational visibility.

Native broker DLQ mechanisms (RabbitMQ DLX, Kafka Connect DLQ SMT) preserve
messages with rich error metadata, but do not write back to the application database.
This consumer bridges that gap for observability dashboards and monitoring.

See Also
--------
- messaging.infrastructure.outbox.outbox_repository : Updates outbox records
- messaging.infrastructure.pubsub.broker_config : Kafka broker configuration
"""

from messaging.infrastructure.pubsub.dlq_bookkeeper.extractors import (
    extract_error_reason,
    extract_event_id,
)
from messaging.infrastructure.pubsub.dlq_bookkeeper.updater import update_db_flag_for_dlq_event

__all__ = [
    "extract_error_reason",
    "extract_event_id",
    "update_db_flag_for_dlq_event",
]


# Example FastStream subscriber registration (to be wired in main.py):
# @broker.subscriber("connect-dlq")  # Kafka Connect DLQ topic
# async def handle_kafka_dlq(
#     msg: dict,
#     headers: dict = Context("message.headers"),
#     app_state = Context("app"),
# ):
#     session_factory = app_state.state.session_factory
#     await update_db_flag_for_dlq_event(msg, headers, session_factory)
#
# @broker.subscriber("rabbitmq-dlq-queue")  # RabbitMQ DLQ queue
# async def handle_rabbitmq_dlq(
#     msg: dict,
#     headers: dict = Context("message.headers"),
#     app_state = Context("app"),
# ):
#     session_factory = app_state.state.session_factory
#     await update_db_flag_for_dlq_event(msg, headers, session_factory)

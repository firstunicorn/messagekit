"""Kafka message processing logic for bridge handler."""

import logging
from typing import Any

from faststream.confluent.annotations import KafkaMessage
from pydantic import ValidationError

from messaging.infrastructure import SqlAlchemyProcessedMessageStore
from messaging.infrastructure.pubsub.bridge.consumer import BridgeConsumer
from messaging.infrastructure.pubsub.rabbit.publisher import RabbitEventPublisher

logger = logging.getLogger(__name__)


async def process_kafka_message(
    message: dict[str, Any],
    msg: KafkaMessage,
    session_factory: Any,
    rabbit_publisher: RabbitEventPublisher,
    routing_key_template: str,
) -> None:
    """Process a single Kafka message and forward to RabbitMQ.

    Args:
        message: Kafka message dict containing event_id and event_type
        msg: KafkaMessage object for manual acknowledgment control
        session_factory: SQLAlchemy async session factory
        rabbit_publisher: RabbitMQ publisher
        routing_key_template: Template for RabbitMQ routing key
    """
    try:
        async with session_factory() as session, session.begin():
            store = SqlAlchemyProcessedMessageStore(session)
            consumer = BridgeConsumer(
                rabbit_publisher=rabbit_publisher,
                processed_message_store=store,
                routing_key_template=routing_key_template,
            )
            await consumer.handle_message(message)

        await msg.ack()

    except ValidationError as e:
        logger.error(
            "Invalid JSON message from Kafka, sending nack",
            extra={
                "event_id": message.get("event_id", "unknown"),
                "error": str(e),
                "message": message,
            },
        )
        await msg.nack()

    except Exception as e:
        logger.error(
            "Bridge handler failed, sending nack for redelivery",
            extra={
                "event_id": message.get("event_id", "unknown"),
                "error_type": type(e).__name__,
                "error": str(e),
            },
            exc_info=True,
        )
        await msg.nack()

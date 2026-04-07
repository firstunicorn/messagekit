"""Database update logic for DLQ events.

Handles marking outbox events as failed when they appear in native DLQ streams.
"""

import logging
from typing import TYPE_CHECKING, Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from messaging.infrastructure.pubsub.dlq_bookkeeper.extractors import (
    extract_error_reason,
    extract_event_id,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


async def update_db_flag_for_dlq_event(
    msg: dict[str, Any],
    headers: dict[str, Any],
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Update outbox_event_record.failed flag for a DLQ event.

    This function is called by FastStream subscribers listening to DLQ topics.
    It extracts the event_id and error reason, then marks the corresponding
    outbox record as failed in the database.

    Args:
        msg: The DLQ message payload
        headers: Message headers (from Context)
        session_factory: SQLAlchemy async session factory

    Raises:
        Exception: If event_id extraction or database update fails
    """
    # Local import to avoid circular dependency
    from messaging.infrastructure.outbox.outbox_repository import SqlAlchemyOutboxRepository

    try:
        event_id = extract_event_id(msg)
        error_reason = extract_error_reason(msg, headers)

        logger.info(
            "Processing DLQ event: event_id=%s, reason=%s",
            event_id,
            error_reason,
        )

        repo = SqlAlchemyOutboxRepository(session_factory)
        await repo.mark_failed(event_id, error_reason)

        logger.info("Marked event %s as failed in database", event_id)

    except Exception as exc:
        logger.error(
            "Failed to update DB flag for DLQ event: %s",
            exc,
            exc_info=True,
            extra={"message": msg, "headers": headers},
        )
        raise

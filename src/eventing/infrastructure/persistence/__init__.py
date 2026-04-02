"""Persistence primitives for eventing infrastructure."""

from eventing.infrastructure.persistence.outbox_orm import OutboxEventRecord
from eventing.infrastructure.persistence.session import create_session_factory

__all__ = ["OutboxEventRecord", "create_session_factory"]

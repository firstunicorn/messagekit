"""Core CRUD operations for outbox events.

This module provides OutboxCrudOperations for handling create and update operations.

See Also
--------
- messaging.infrastructure.outbox.outbox_queries : Query operations
- messaging.infrastructure.outbox.outbox_repository : The facade repository
"""

from messagekit.infrastructure.outbox.outbox_crud.operations import OutboxCrudOperations

__all__ = ["OutboxCrudOperations"]

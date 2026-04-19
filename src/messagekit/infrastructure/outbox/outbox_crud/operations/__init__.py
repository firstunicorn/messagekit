"""Outbox CRUD operations - re-exports."""

from messagekit.infrastructure.outbox.outbox_crud.operations.crud_operations import (
    OutboxCrudOperations,
)

__all__ = ["OutboxCrudOperations"]

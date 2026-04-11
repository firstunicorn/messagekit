# AttributeError: async_sessionmaker has no 'in_transaction' — bridge idempotency broken

**Date:** 2026-04-11
**Status:** Fixed ✅
**Severity:** Critical — idempotency checks completely broken in production bridge consumer

## Symptom

`AttributeError: 'async_sessionmaker' object has no attribute 'in_transaction'` when bridge consumed Kafka messages. `SqlAlchemyProcessedMessageStore` failed to check if message was already processed, allowing duplicate RabbitMQ publishes.

## Root cause

`SqlAlchemyProcessedMessageStore.__init__` expects `AsyncSession` instance but received `async_sessionmaker` (factory). The store was instantiated as a singleton in `lifespan()` with `session_factory` parameter instead of an actual session.

```python
# WRONG (in lifespan.py):
processed_message_store = SqlAlchemyProcessedMessageStore(session_factory)  # session_factory is async_sessionmaker

# CORRECT (per-message in _initialization.py):
async with session_factory() as session, session.begin():
    store = SqlAlchemyProcessedMessageStore(session)  # session is AsyncSession
```

## Why it happened

Original architecture treated `SqlAlchemyProcessedMessageStore` as a singleton shared across all messages. This conflated session lifecycle (per-request) with store lifecycle (per-message). The store was initialized once at app startup with the factory, not with an active session.

## Fix

Refactored `register_bridge_handler` in `src/messaging/main/_initialization.py`:
- Removed singleton `BridgeConsumer` and `SqlAlchemyProcessedMessageStore`
- Instantiate both per message within `async with session_factory() as session, session.begin():`
- Each message gets fresh `AsyncSession`, atomic transaction for claim → publish
- Combined `with` statement satisfies Ruff SIM117 (nested context managers)

## Why session.begin() matters

Without `begin()`, SQLAlchemy uses autocommit mode. The idempotency claim (INSERT...ON CONFLICT) would commit even if RabbitMQ publish fails, causing message loss. `begin()` ensures atomic: claim + publish succeed together, or both rollback.

## Files changed

- `src/messaging/main/_initialization.py` — per-message session/store instantiation
- `src/messaging/main/lifespan.py` — removed singleton instantiation, updated handler registration

## Lessons

- SQLAlchemy `async_sessionmaker` is a factory, not a session — never pass it where `AsyncSession` is expected
- Singleton pattern doesn't work for per-message database operations
- `session.begin()` is required for atomic multi-operation transactions (not just single queries)

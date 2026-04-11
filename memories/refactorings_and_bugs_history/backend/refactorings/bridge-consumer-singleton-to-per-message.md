# Bridge consumer: singleton → per-message instantiation

**Date:** 2026-04-11
**Status:** Documented ✅
**Type:** Refactoring

## Before

`BridgeConsumer` and `SqlAlchemyProcessedMessageStore` were singletons initialized once in `lifespan()`:

```python
# In lifespan.py — WRONG:
processed_message_store = SqlAlchemyProcessedMessageStore(session_factory)
bridge_consumer = BridgeConsumer(rabbit_publisher, processed_message_store)
```

Problems:
- `session_factory` (async_sessionmaker) passed instead of `AsyncSession` → AttributeError
- Shared state across all messages → no transaction isolation
- Connection lifecycle not managed per message → potential leaks

## After

Both instantiated per message within session context in `register_bridge_handler`:

```python
@broker.subscriber(bridge_config.kafka_topic)
async def handle_kafka_event(message: dict[str, Any]) -> None:
    async with session_factory() as session, session.begin():
        store = SqlAlchemyProcessedMessageStore(session)
        consumer = BridgeConsumer(rabbit_publisher, store)
        await consumer.handle_message(message)
```

Benefits:
- Fresh `AsyncSession` per message (not factory)
- Atomic transaction: claim → publish → commit/rollback
- Proper connection lifecycle (session closed after each message)
- Idempotency enforced at message level

## Why session.begin()

Without `begin()`, SQLAlchemy uses autocommit. The idempotency claim (INSERT...ON CONFLICT) would commit even if RabbitMQ publish fails, causing message loss. `begin()` ensures atomic: both succeed or both rollback.

## Why combined `with`

Ruff SIM117 requires combining nested async context managers. `async with session_factory() as session, session.begin():` is equivalent to nested statements but satisfies the rule.

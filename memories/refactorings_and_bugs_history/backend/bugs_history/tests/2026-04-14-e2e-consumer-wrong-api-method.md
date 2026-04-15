# Bug: E2E consumer used non-existent was_processed() method

**[Summary](#summary)** • **[Root Cause](#root-cause)** • **[Fix](#fix)** • **[Prevention](#prevention)**

## Summary

E2E v2 test consumer called `store.was_processed(message_id)` which doesn't exist on `SqlAlchemyProcessedMessageStore`. The correct API is `claim()` which returns whether the event is new (not already processed).

**Date**: 2026-04-14  
**Severity**: Critical (test crash)  
**Status**: ✅ Fixed

## Symptoms

```
ERROR - AttributeError: 'SqlAlchemyProcessedMessageStore' object has no attribute 'was_processed'
    was_processed = await store.was_processed(message_id)
AttributeError: 'SqlAlchemyProcessedMessageStore' object has no attribute 'was_processed'
```

Consumer crashed on every message with `AttributeError`.

## Root cause

### Wrong code (E2E test)

```python
# scripts/tests/e2e_v2/consumer_service_v2.py (BEFORE)
store = SqlAlchemyProcessedMessageStore(session)

async with session.begin():
    was_processed = await store.was_processed(message_id)  # ❌ Method doesn't exist
    
    if was_processed:
        logger.info("Already processed")
        return
    
    # Process and mark
    await store.mark_processed(
        message_id=message_id,
        event_type=message.get("eventType", "unknown"),
        payload=message
    )
```

### Correct API (actual implementation)

```python
# src/messaging/infrastructure/persistence/processed_message_store/processed_message_store.py
class SqlAlchemyProcessedMessageStore(IProcessedMessageStore):
    async def claim(self, *, consumer_name: str, event_id: str) -> bool:
        """Return whether this consumer may process the given event identifier.
        
        Returns:
            bool: True if the event was claimed (first processing attempt),
                False if the event was already claimed (duplicate, idempotent skip).
        """
        # Attempts INSERT with ON CONFLICT DO NOTHING
        # Returns True if insert succeeded (new), False if duplicate
```

The store implements idempotency via **database insert with conflict handling**, not a separate "check then insert" pattern.

### Why it happened

The E2E test invented its own API instead of checking the actual `SqlAlchemyProcessedMessageStore` interface. The store uses an insert-based claiming pattern (atomic operation) rather than separate check/mark methods.

## Fix applied

```python
# scripts/tests/e2e_v2/consumer_service_v2.py (AFTER)
store = SqlAlchemyProcessedMessageStore(session)

async with session.begin():
    # claim() returns True if new (not processed), False if already processed
    is_new = await store.claim(
        consumer_name="e2e-consumer-v2",
        event_id=str(message_id)
    )
    
    if not is_new:
        logger.info(f"⚠️  Message {message_id} already processed (idempotent skip)")
        return
    
    # Process - no need to mark_processed(), claim() already did it
    logger.info("✅ Message is new, processing...")
    self.received_events.append(message)
```

Key differences:
1. Use `claim()` not `was_processed()`
2. `claim()` requires `consumer_name` parameter (identifies which consumer is claiming)
3. `claim()` does insert atomically (no separate `mark_processed()` needed)
4. Return value inverted: `True` = new (process), `False` = duplicate (skip)

## Verification

After fix, idempotency works correctly:

```
First message:
✅ Message 61a51d19-f5e1-4336-8b06-17f6d335fefe claimed and processed
✅ Found 1 processed messages in consumer_db

Duplicate message:
⚠️  Message 61a51d19-f5e1-4336-8b06-17f6d335fefe already processed (idempotent skip)
✅ Found 1 processed messages in consumer_db (still 1, duplicate rejected)
```

## Prevention

### For future E2E tests

1. **Check actual interface**: Read the store implementation before using it
2. **Look at production usage**: Check how production bridge consumer uses the store
3. **Run type checker**: `mypy` would have caught this (`SqlAlchemyProcessedMessageStore` has no attribute `was_processed`)

### Production pattern (reference)

```python
# src/messaging/infrastructure/pubsub/bridge/consumer.py (line 42-46)
is_new = await self._processed_store.claim(
    consumer_name="kafka_rabbitmq_bridge", 
    event_id=event_id
)
if not is_new:
    return  # Already processed
```

### Key points about claim() API

- **Atomic operation**: Insert happens inside `claim()`, handles race conditions
- **Consumer name required**: Tracks which consumer processed the event
- **Returns boolean**: `True` = first time (process), `False` = duplicate (skip)
- **Transaction aware**: Starts transaction if not active, caller must commit
- **No separate mark_processed()**: The insert IS the marking

## References

- Store implementation: `src/messaging/infrastructure/persistence/processed_message_store/processed_message_store.py` (line 32)
- Production usage: `src/messaging/infrastructure/pubsub/bridge/consumer.py` (line 42)
- Fixed file: `scripts/tests/e2e_v2/consumer_service_v2.py` (line 104)

## Related bugs

- [Wrong event ID field names](./2026-04-14-e2e-consumer-wrong-event-id-field.md)
- [Wrong data access pattern](./2026-04-14-e2e-consumer-wrong-data-access.md)

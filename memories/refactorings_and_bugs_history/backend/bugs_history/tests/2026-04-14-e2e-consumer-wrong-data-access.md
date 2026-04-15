# Bug: E2E consumer used nested data access instead of camelCase

**[Summary](#summary)** • **[Root Cause](#root-cause)** • **[Fix](#fix)** • **[Prevention](#prevention)**

## Summary

E2E v2 test consumer tried to access `message.get('data', {}).get('user_id')` assuming a nested structure, but `BaseEvent` serializes fields directly in camelCase. The correct access is `message.get('userId')`.

**Date**: 2026-04-14  
**Severity**: Low (non-critical field, didn't cause test failure)  
**Status**: ✅ Fixed

## Symptoms

```python
user_id = message.get('data', {}).get('user_id')  # Always None
logger.info(f"Processing event for user_id: {user_id}")  # Logs: user_id: None
```

Field was always `None`, but didn't cause test failure since it's not used for critical logic.

## Root cause

### Wrong code (E2E test)

```python
# scripts/tests/e2e_v2/consumer_service_v2.py (BEFORE)
user_id = message.get('data', {}).get('user_id')  # ❌ Nested structure doesn't exist
logger.info(f"Processing event for user_id: {user_id}")  # Logs None
```

This assumes a message structure like:
```json
{
  "eventId": "...",
  "data": {
    "user_id": 98765  // ❌ Doesn't exist
  }
}
```

### Actual message structure

```json
{
  "eventId": "89d6fc6c-cb61-4057-ad38-c74bf9a0d7e4",
  "eventType": "test.event_emitted_v2",
  "occurredAt": "2026-04-14T20:47:39.723795+00:00",
  "aggregateId": "test-agg-v2-001",
  "userId": 98765,  // ✅ Direct camelCase field
  "action": "account_created",
  "source": "e2e-test-v2"
}
```

Fields are serialized directly in camelCase, not nested under a `data` key.

### Why it happened

`BaseEvent` uses Pydantic's `to_camel` alias generator which converts Python snake_case to JSON camelCase:

```python
# src/messaging/core/contracts/base_event.py
class BaseEvent(IOutboxEvent, BaseDomainEvent):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    
    # Python field names (snake_case)
    event_id: UUID
    event_type: str
    user_id: int  # etc.
    
    # Serializes to JSON as (camelCase)
    # {
    #   "eventId": "...",
    #   "eventType": "...",
    #   "userId": 98765
    # }
```

There is **no nested `data` object** in the serialized JSON.

## Fix applied

```python
# scripts/tests/e2e_v2/consumer_service_v2.py (AFTER)
user_id = message.get('userId')  # ✅ Direct camelCase field
logger.info(f"Processing event for userId: {user_id}")  # Logs: userId: 98765
```

## Verification

After fix, field is correctly accessed:

```
Processing event for userId: 98765  # ✅ Correct value
```

## Prevention

### For future E2E tests

1. **Check BaseEvent serialization**: Look at `model_config = ConfigDict(alias_generator=to_camel)`
2. **Inspect actual messages**: Use `kafka-console-consumer` to see real JSON
3. **Reference test event definition**: Check `scripts/tests/e2e_v2/shared_events_v2.py`

### BaseEvent field mapping

| Python (snake_case) | JSON (camelCase) |
|---------------------|------------------|
| `event_id` | `eventId` |
| `event_type` | `eventType` |
| `aggregate_id` | `aggregateId` |
| `user_id` | `userId` |
| `occurred_at` | `occurredAt` |
| `correlation_id` | `correlationId` |
| `causation_id` | `causationId` |

### Test event structure

```python
# scripts/tests/e2e_v2/shared_events_v2.py
class TestEventV2(BaseEvent):
    event_type: str = "test.event_emitted_v2"
    source: str = "e2e-test-v2"
    aggregate_id: str
    user_id: int  # ← Serializes to "userId" in JSON
    action: str
    metadata: dict[str, Any] = {}
```

Serializes to:
```json
{
  "eventType": "test.event_emitted_v2",
  "source": "e2e-test-v2",
  "aggregateId": "test-agg-v2-001",
  "userId": 98765,
  "action": "account_created",
  "metadata": {}
}
```

## Impact

**Why low severity**: The `user_id` field was only used for logging in the E2E test, not for critical processing logic. The bug didn't cause test failure, just logged `None` instead of the actual value.

**But important to fix**: In production consumers, incorrect field access could cause:
- Logic errors (wrong user processed)
- Null pointer exceptions
- Failed business rules validation

## References

- BaseEvent definition: `src/messaging/core/contracts/base_event.py`
- Test event: `scripts/tests/e2e_v2/shared_events_v2.py`
- Fixed file: `scripts/tests/e2e_v2/consumer_service_v2.py` (line 114)

## Related bugs

- [Wrong event ID field names](./2026-04-14-e2e-consumer-wrong-event-id-field.md)
- [Wrong API method: was_processed vs claim](./2026-04-14-e2e-consumer-wrong-api-method.md)

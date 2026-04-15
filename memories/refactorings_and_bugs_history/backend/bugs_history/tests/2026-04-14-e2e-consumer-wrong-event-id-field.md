# Bug: E2E consumer used wrong event ID field names

**[Summary](#summary)** • **[Root Cause](#root-cause)** • **[Fix](#fix)** • **[Prevention](#prevention)**

## Summary

E2E v2 test consumer looked for `id` or `messageId` fields, but Kafka messages contain `event_id` (snake_case) or `eventId` (camelCase). This caused consumer to skip all messages without processing them to database.

**Date**: 2026-04-14  
**Severity**: High (test false positive)  
**Status**: ✅ Fixed

## Symptoms

```
Consumer logs:
⚠️  No message ID found in message
⚠️  No message ID found in message
...
Result: Received 10 messages, processed 0 to database
```

Consumer received messages from Kafka but immediately returned without processing because it couldn't find the event ID.

## Root cause

### Wrong code (E2E test)

```python
# scripts/tests/e2e_v2/consumer_service_v2.py (BEFORE)
message_id = message.get("id") or message.get("messageId")
if not message_id:
    logger.warning("⚠️  No message ID found in message")
    self.received_events.append(message)
    return  # ❌ Exits without processing to database
```

### Correct pattern (production)

```python
# src/messaging/infrastructure/pubsub/bridge/consumer.py (line 36)
event_id = message.get("event_id") or message.get("eventId")
if not event_id:
    return  # Skip malformed messages
```

### Why it happened

`BaseEvent` uses snake_case field names internally (`event_id`) but serializes to camelCase JSON (`eventId`) via Pydantic:

```python
# src/messaging/core/contracts/base_event.py
class BaseEvent(IOutboxEvent, BaseDomainEvent):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    
    event_id: UUID = Field(default_factory=uuid4)  # Internal: event_id
    # Serializes to JSON as: "eventId": "..."
```

E2E test looked for `id` or `messageId` which don't exist in the message structure.

### Kafka message structure (actual)

```json
{
  "eventId": "89d6fc6c-cb61-4057-ad38-c74bf9a0d7e4",
  "eventType": "test.event_emitted_v2",
  "occurredAt": "2026-04-14T20:47:39.723795+00:00",
  "aggregateId": "test-agg-v2-001",
  "userId": 98765,
  "action": "account_created"
}
```

Note: Field is `eventId` (camelCase), not `id` or `messageId`.

## Fix applied

```python
# scripts/tests/e2e_v2/consumer_service_v2.py (AFTER)
# Extract event ID (match production code: event_id or eventId)
message_id = message.get("event_id") or message.get("eventId")
if not message_id:
    logger.warning("⚠️  No event ID found in message")
    self.received_events.append(message)
    return
```

## Verification

After fix, consumer correctly processes messages:

```
✅ Message 61a51d19-f5e1-4336-8b06-17f6d335fefe claimed and processed
✅ Found 1 processed messages in consumer_db
```

## Prevention

### For future E2E tests

1. **Always check production patterns first**: Look at production consumer code for field names
2. **Inspect actual Kafka messages**: Use `kafka-console-consumer` to see real JSON structure
3. **Verify against BaseEvent**: Check `BaseEvent` serialization config (`alias_generator=to_camel`)

### Code review checklist

- [ ] Event ID accessed as `event_id` or `eventId` (not `id` or `messageId`)
- [ ] Consumer field access matches production bridge consumer pattern
- [ ] Test includes database verification (not just "received" count)

## References

- Production pattern: `src/messaging/infrastructure/pubsub/bridge/consumer.py` (line 36)
- BaseEvent definition: `src/messaging/core/contracts/base_event.py` (line 30)
- Fixed file: `scripts/tests/e2e_v2/consumer_service_v2.py` (line 92)

## Related bugs

- [Wrong API method: was_processed vs claim](./2026-04-14-e2e-consumer-wrong-api-method.md)
- [Wrong data access: nested vs camelCase](./2026-04-14-e2e-consumer-wrong-data-access.md)

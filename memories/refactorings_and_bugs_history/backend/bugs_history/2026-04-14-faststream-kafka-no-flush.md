# Bug: FastStream KafkaBroker doesn't flush messages by default (production)

**[Summary](#summary)** • **[Root Cause](#root-cause)** • **[Fix](#fix)** • **[Impact](#impact)**

## Summary

`KafkaEventPublisher` used `broker.publish()` which buffers messages for batching performance but never flushes them to Kafka. Manual replay operations reported success but messages were never sent.

**Date**: 2026-04-14  
**Severity**: High (production bug in manual replay)  
**Component**: `OutboxReplayService`  
**Status**: ✅ Fixed

## Symptoms

E2E v2 test revealed:
```
Producer:
✅ Message queued for Kafka: test.event_emitted_v2
✅ All messages flushed to Kafka

Verification:
$ kafka-console-consumer --topic test.event_emitted_v2 --from-beginning
Processed a total of 0 messages  # ❌ No messages in Kafka!
```

Producer reported success, but `kafka-console-consumer` showed 0 messages. Messages were buffered in memory, never sent.

## Root cause

### Production code (before)

```python
# src/messaging/infrastructure/pubsub/kafka_publisher.py
class KafkaEventPublisher(IEventPublisher):
    def __init__(self, broker: KafkaBroker) -> None:
        self._broker = broker
    
    async def publish_to_topic(self, topic: str, message: dict[str, Any]) -> None:
        await self._broker.publish(message, topic=topic, key=key_bytes)
        # ❌ No flush - messages buffered indefinitely
```

### FastStream default behavior

FastStream's `KafkaBroker.publish()` **does not flush by default**. It buffers messages for batching to improve throughput:

```python
# FastStream behavior
broker = KafkaBroker("localhost:9092")
await broker.publish({"data": "test"}, topic="events")
# Message is QUEUED, not sent to Kafka
# Will be flushed when:
# 1. Batch is full (default ~100 messages)
# 2. Linger time expires (default 0ms, but still batches)
# 3. Broker is closed/stopped
# 4. autoflush=True is set
```

For low-volume operations (like manual replay), messages never reach batch size and sit in buffer forever.

## Discovery

E2E v2 test initially used FastStream's `broker.publish()` but messages never reached Kafka. Switching to `confluent_kafka.Producer` with explicit `flush()` revealed the issue:

```python
# E2E test fix (scripts/tests/e2e_v2/producer_service_v2.py)
from confluent_kafka import Producer

producer = Producer({'bootstrap.servers': 'localhost:9092'})
producer.produce(topic, value)
unflushed = producer.flush(timeout=10.0)  # ✅ Explicit flush required
```

After flush, messages appeared in Kafka immediately.

## FastStream autoflush feature

FastStream added `autoflush` parameter in **April 2025** (Issue #2179, PR #2182):

```python
# Solution 1: Use autoflush=True
publisher = broker.publisher("topic", autoflush=True)
await publisher.publish(message)  # ✅ Flushes after every publish
```

Documentation: https://faststream.ag2.ai/latest/api/faststream/confluent/broker/broker/KafkaBroker/

## Fix applied

### Updated KafkaEventPublisher

```python
# src/messaging/infrastructure/pubsub/kafka_publisher.py
class KafkaEventPublisher(IEventPublisher):
    def __init__(self, broker: KafkaBroker, autoflush: bool = False) -> None:
        """Initialize publisher with optional autoflush.
        
        Args:
            broker: FastStream Kafka broker instance
            autoflush: If True, flush after every publish (default: False)
        """
        self._broker = broker
        self._autoflush = autoflush
    
    async def publish_to_topic(self, topic: str, message: dict[str, Any]) -> None:
        if self._autoflush:
            publisher = self._broker.publisher(topic, autoflush=True)
            await publisher.publish(message, key=key_bytes)  # ✅ Flushes
        else:
            await self._broker.publish(message, topic=topic, key=key_bytes)
```

### Updated replay service

```python
# src/messaging/presentation/dependencies/replay.py
async def get_replay_service(...) -> AsyncIterator[OutboxReplayService]:
    queries = OutboxReplayQueries(session)
    broker = request.app.state.broker
    # Use autoflush=True for replay operations to ensure immediate delivery
    publisher = KafkaEventPublisher(broker, autoflush=True)  # ✅ Fixed
    service = OutboxReplayService(queries, publisher)
    yield service
```

## Impact

| Component | Before | After | Status |
|-----------|--------|-------|--------|
| **Manual Replay** | Messages buffered, not sent | Messages flushed immediately | ✅ Fixed |
| **Normal Publishing** | Not affected (uses Kafka Connect CDC) | Not affected | ✅ Safe |
| **E2E Tests** | Used confluent_kafka.Producer | Still uses explicit flush | ✅ Correct |

### Why normal publishing is unaffected

The main application flow doesn't use `KafkaEventPublisher`:

```
Normal flow:
Application → Outbox Table → Kafka Connect CDC → Kafka
(NOT using KafkaEventPublisher)

Manual replay:
Admin API → OutboxReplayService → KafkaEventPublisher → Kafka
(Fixed with autoflush=True)
```

## When to use autoflush

### Use autoflush=True when:
- **Manual replay operations** (low volume, need immediate delivery)
- **Admin endpoints** that publish events
- **Debugging/testing** scenarios
- **Critical real-time events** that can't be batched

### Don't use autoflush when:
- **High-throughput operations** (kills performance)
- **Batch processing** (defeats the purpose of batching)
- **Normal app publishing** (should use Kafka Connect CDC anyway)

## Performance considerations

```python
# Without autoflush (batched, fast)
for i in range(1000):
    await publisher.publish(msg)  # Buffered
# Batch sent once when full or on timeout

# With autoflush (immediate, slower)
publisher = broker.publisher("topic", autoflush=True)
for i in range(1000):
    await publisher.publish(msg)  # Each message flushed individually
# 1000 network round trips!
```

**Rule of thumb**: Use autoflush for operations that publish < 10 messages. For bulk operations, buffer and flush manually.

## Prevention

### For new publishers

1. **Document flush requirements**: Add docstring noting autoflush behavior
2. **Consider use case**: Low volume = autoflush, high volume = buffered
3. **Test with kafka-console-consumer**: Verify messages actually reach Kafka
4. **Add delivery callbacks**: Confirm successful delivery

### E2E test pattern

Always use `confluent_kafka.Producer` with explicit flush for tests:

```python
from confluent_kafka import Producer

producer = Producer({'bootstrap.servers': 'localhost:9092'})

def delivery_callback(err, msg):
    if err:
        logger.error(f"Delivery failed: {err}")
    else:
        logger.info(f"Delivered to partition {msg.partition()} offset {msg.offset()}")

producer.produce(topic, value, callback=delivery_callback)
unflushed = producer.flush(timeout=10.0)
assert unflushed == 0, "Messages failed to flush"
```

## References

- Fixed file: `src/messaging/infrastructure/pubsub/kafka_publisher.py`
- Replay service: `src/messaging/presentation/dependencies/replay.py`
- E2E test pattern: `scripts/tests/e2e_v2/producer_service_v2.py`
- FastStream docs: https://faststream.ag2.ai/latest/api/faststream/confluent/broker/broker/KafkaBroker/
- GitHub Issue: https://github.com/ag2ai/faststream/issues/2179
- Lesson: `memories/lessons-for-ai/universal/messaging/faststream-kafka-flush.md`

## Related E2E bugs

- [Wrong event ID field names](./2026-04-14-e2e-consumer-wrong-event-id-field.md)
- [Wrong API method: was_processed vs claim](./2026-04-14-e2e-consumer-wrong-api-method.md)
- [Wrong data access pattern](./2026-04-14-e2e-consumer-wrong-data-access.md)

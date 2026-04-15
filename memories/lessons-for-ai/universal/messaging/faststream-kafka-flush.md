# FastStream Kafka flush mechanism

**[Critical](#critical)** • **[Usage](#usage)** • **[Production Fix](#production-fix)** • **[E2E Pattern](#e2e-pattern)**

## Critical rule

FastStream's `broker.publish()` **does not flush by default**. Messages are buffered for batching performance. For guaranteed immediate delivery, use `autoflush=True` or explicit `confluent_kafka.Producer.flush()`.

## Problem discovered

E2E v2 tests revealed that `FastStream.KafkaBroker.publish()` queues messages but doesn't flush them to Kafka. The producer reported success, but `kafka-console-consumer` showed 0 messages.

```python
# ❌ DOESN'T WORK - Messages buffered, not sent
broker = KafkaBroker("localhost:9092")
await broker.publish({"data": "test"}, topic="events")
# Message queued but NOT in Kafka!
```

## Solution 1: FastStream autoflush (recommended for production)

FastStream added `autoflush` parameter in April 2025 (Issue #2179, PR #2182).

```python
# ✅ WORKS - Flushes after every publish
broker = KafkaBroker("localhost:9092")
publisher = broker.publisher("events", autoflush=True)
await publisher.publish({"data": "test"})
```

**When to use:**
- Manual replay operations (`OutboxReplayService`)
- Admin endpoints that publish events
- Any scenario requiring immediate delivery guarantee

**When NOT to use:**
- High-throughput batch operations (autoflush kills performance)
- Normal app publishing (uses Kafka Connect CDC, not `KafkaEventPublisher`)

## Solution 2: confluent_kafka.Producer with explicit flush (E2E tests)

For testing or when you need direct control:

```python
from confluent_kafka import Producer

producer = Producer({
    'bootstrap.servers': 'localhost:9092',
    'client.id': 'test-producer'
})

def delivery_callback(err, msg):
    if err:
        logger.error(f"Delivery failed: {err}")
    else:
        logger.info(f"Delivered to {msg.topic()} partition {msg.partition()} offset {msg.offset()}")

producer.produce(
    topic="events",
    value=json.dumps({"data": "test"}).encode(),
    callback=delivery_callback
)

# CRITICAL: Flush to actually send messages
unflushed = producer.flush(timeout=10.0)
if unflushed > 0:
    logger.error(f"{unflushed} messages failed to flush")
```

## Production fix applied

### Before (no flush)
```python
class KafkaEventPublisher(IEventPublisher):
    def __init__(self, broker: KafkaBroker) -> None:
        self._broker = broker
    
    async def publish_to_topic(self, topic: str, message: dict[str, Any]) -> None:
        await self._broker.publish(message, topic=topic, key=key_bytes)
        # ❌ No flush - messages buffered
```

### After (configurable autoflush)
```python
class KafkaEventPublisher(IEventPublisher):
    def __init__(self, broker: KafkaBroker, autoflush: bool = False) -> None:
        self._broker = broker
        self._autoflush = autoflush
    
    async def publish_to_topic(self, topic: str, message: dict[str, Any]) -> None:
        if self._autoflush:
            publisher = self._broker.publisher(topic, autoflush=True)
            await publisher.publish(message, key=key_bytes)
            # ✅ Flushes after publish
        else:
            await self._broker.publish(message, topic=topic, key=key_bytes)
            # Buffered for performance
```

### Replay service updated
```python
# src/messaging/presentation/dependencies/replay.py
async def get_replay_service(...) -> AsyncIterator[OutboxReplayService]:
    broker = request.app.state.broker
    publisher = KafkaEventPublisher(broker, autoflush=True)  # ✅ Immediate delivery
    service = OutboxReplayService(queries, publisher)
    yield service
```

## E2E pattern

E2E v2 tests use `confluent_kafka.Producer` directly:

```python
# scripts/tests/e2e_v2/producer_service_v2.py
self.kafka_producer = Producer({
    'bootstrap.servers': 'localhost:9092',
    'client.id': 'e2e-producer-v2'
})

# Publish with delivery confirmation
producer.produce(topic, value, callback=delivery_callback)

# CRITICAL: Flush before assertions
unflushed = producer.flush(timeout=10.0)
assert unflushed == 0, "Messages failed to flush"
```

## Why normal publishing is unaffected

The main application flow doesn't use `KafkaEventPublisher`:

```
Application → Outbox Table → Kafka Connect CDC → Kafka
```

Not:
```
Application → KafkaEventPublisher → Kafka  # ❌ Only used for manual replay
```

## References

- FastStream autoflush docs: https://faststream.ag2.ai/latest/api/faststream/confluent/broker/broker/KafkaBroker/
- GitHub Issue #2179: Feature: confluent autoflush
- GitHub PR #2182: feat: auto flush confluent broker
- E2E test: `scripts/tests/e2e_v2/producer_service_v2.py`
- Production code: `src/messaging/infrastructure/pubsub/kafka_publisher.py`

## Summary

- **Default behavior**: Buffered (no flush) for performance
- **Autoflush=True**: Flush after every publish (slower but guaranteed delivery)
- **Production impact**: Only affects `OutboxReplayService` (fixed)
- **Normal publishing**: Uses Kafka Connect CDC (unaffected)
- **E2E tests**: Use `confluent_kafka.Producer` with explicit `flush()`

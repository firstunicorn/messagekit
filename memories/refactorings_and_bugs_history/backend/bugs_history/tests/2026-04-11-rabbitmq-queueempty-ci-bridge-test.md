# RabbitMQ QueueEmpty in CI — test_bridge_publishes_to_rabbitmq

**Date:** 2026-04-11
**Status:** Fixed ✅
**Severity:** Critical — bridge integration test failing across all CI environments (Windows, WSL2, GitHub Actions)

## Symptom

`aio_pika.exceptions.QueueEmpty` in `test_bridge_publishes_to_rabbitmq`. Test published message to Kafka, set up RabbitMQ queue, but `queue.get(timeout=30)` returned None — message never arrived.

## Root causes (multiple, discovered sequentially)

### 1. Race condition: queue setup after publish
Test originally set up RabbitMQ queue AFTER publishing to Kafka. Bridge consumed message before queue existed.

**Fix:** Reordered test to declare queue and bind to exchange BEFORE publishing to Kafka.

### 2. Implicit DIRECT exchange type
`RabbitEventPublisher.__init__` accepted bare string `"events"` as default_exchange. FastStream's `broker.publish()` used implicit DIRECT exchange type. DIRECT requires exact routing key match; test queue bound to TOPIC exchange pattern. Message routed to wrong exchange type silently.

**Fix:** Explicitly construct `RabbitExchange(name, type=ExchangeType.TOPIC, durable=True)` when string is passed.

### 3. Kafka consumer not joined consumer group
`FastStream broker.start()` returns before consumer group rebalancing completes. Tests published messages before bridge consumer was polling.

**Fix:** Added 5-second `asyncio.sleep()` in `async_client_with_kafka` fixture after lifespan initialization. Kafka rebalancing takes 2-3s; 5s buffer for slow CI.

### 4. CI environment slowness
GitHub Actions (Docker-in-Docker) measured latency: Kafka poll 1-2s, DB query 500ms, RabbitMQ publish 500ms (total 8-12s vs <1s locally).

**Fix:** Increased `asyncio.sleep` to 15s and `queue.get` timeout to 30s.

### 5. Idempotency store collisions
Hardcoded `event_id` ("bridge-test-2") caused false negatives when test matrix ran in parallel (3.10/3.11/3.12). `SqlAlchemyProcessedMessageStore` claims by event_id; incomplete DB cleanup between runs caused bridge to skip "already processed" messages.

**Fix:** Use `uuid4()` for event_id per test invocation.

## Files changed

- `src/messaging/infrastructure/pubsub/rabbit/publisher.py` — explicit TOPIC exchange
- `tests/conftest.py` — 5s consumer wait, setattr() for Pydantic settings
- `tests/integration/test_kafka_rabbitmq_bridge.py` — UUID, increased timeouts

## Lessons

- FastStream broker.start() is async but doesn't wait for consumer readiness
- Bare string exchange names default to DIRECT, not TOPIC
- CI environments (GitHub Actions) can be 10x slower than local for containerized brokers
- Hardcoded test IDs cause false negatives in parallel test matrices

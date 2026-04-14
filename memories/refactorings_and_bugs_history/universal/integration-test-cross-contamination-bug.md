# Integration test cross-contamination bug

**[Problem](#problem)** • **[Root cause](#root-cause)** • **[Symptoms](#symptoms)** • **[Solution](#solution)**

## Problem

Integration tests were failing with assertion errors showing unexpected data counts or states, but only when run together. Tests passed when run individually.

```
FAILED tests/integration/test_bridge_handler_integration/test_idempotency.py::test_prevents_duplicate_publishing - AssertionError: assert 2 == 1
```

Expected 1 message, found 2. Second message was from a different test.

## Root cause analysis

**Shared infrastructure resources caused cross-contamination**:

1. **Kafka consumer groups**: Hardcoded `group_id="eventing-consumers"` in production code
   - All tests shared same consumer group
   - Offset tracking was shared between tests
   - Messages from one test visible to another test

2. **RabbitMQ exchanges**: Tests used same exchange name `"test-events"`
   - Messages published by one test visible to other tests
   - Queues bound to shared exchange received cross-test messages

3. **Test execution order dependency**:
   - `test_idempotency.py` ran first: published 1 message to shared infrastructure
   - `test_exception_nack.py` ran second: saw leftover message from previous test
   - Assertions failed due to unexpected state

## Symptoms

**During CI**:
```
Tests passed: 0
Tests failed: 7

test_idempotency.py::test_prevents_duplicate_publishing FAILED
  AssertionError: assert 2 == 1

test_exception_nack.py::test_handles_exception FAILED  
  AssertionError: assert 3 == 1
```

**When run individually**:
```bash
pytest tests/integration/test_idempotency.py -v
# PASSED

pytest tests/integration/test_exception_nack.py -v  
# PASSED
```

**Locally vs CI**:
- Local: Tests often passed (lucky execution order)
- CI: Tests consistently failed (parallel execution)

## Error details

### Test isolation violation 1: Shared Kafka consumer group

**Production code**:
```python
# src/messaging/main/_initialization/bridge_setup/handler_registration.py
async def register_bridge_subscriber(
    kafka_broker: KafkaBroker,
    bridge_config: BridgeConfig,
    bridge: KafkaToRabbitBridge,
) -> None:
    @kafka_broker.subscriber(
        bridge_config.kafka_topic,
        group_id="eventing-consumers",  # ❌ HARDCODED
        ack_policy=AckPolicy.MANUAL,
    )
```

**Problem**: All tests used same consumer group, causing offset and message cross-contamination.

### Test isolation violation 2: Shared RabbitMQ exchange

**Test code**:
```python
# tests/integration/test_bridge_handler_integration/test_idempotency.py
async def test_prevents_duplicate_publishing():
    kafka_bootstrap, rabbitmq_url, consumer_group_id = setup_test_containers_config(
        monkeypatch,
        kafka_container.get_bootstrap_server(),
        rabbit_container.get_connection_url(),
        exchange="test-events",  # ❌ SHARED
    )
```

**Problem**: Multiple tests published to same exchange, messages visible across tests.

### Test isolation violation 3: Non-configurable infrastructure IDs

**Setup helper**:
```python
# tests/integration/test_bridge_handler_integration/setup_helpers.py
def setup_test_containers_config(
    monkeypatch: pytest.MonkeyPatch,
    kafka_bootstrap: str,
    rabbitmq_url: str,
) -> tuple[str, str]:
    # ❌ No way to pass unique IDs per test
    monkeypatch.setenv("KAFKA_BOOTSTRAP_SERVERS", kafka_bootstrap)
    monkeypatch.setenv("RABBITMQ_URL", rabbitmq_url)
    return kafka_bootstrap, rabbitmq_url
```

**Problem**: Tests couldn't specify unique resource identifiers even if they wanted to.

## Solution

### 1. Make consumer group configurable in production code

**Modified `BridgeConfig`**:
```python
# src/messaging/infrastructure/pubsub/bridge/config.py
@dataclass(frozen=True, slots=True)
class BridgeConfig:
    kafka_topic: str
    rabbitmq_exchange: str
    routing_key_template: str
    consumer_group_id: str  # ✅ NEW FIELD
```

**Modified handler registration**:
```python
# src/messaging/main/_initialization/bridge_setup/handler_registration.py
@kafka_broker.subscriber(
    bridge_config.kafka_topic,
    group_id=bridge_config.consumer_group_id,  # ✅ FROM CONFIG
    ack_policy=AckPolicy.MANUAL,
)
```

### 2. Added unique resource IDs to setup helper

**Modified setup helper**:
```python
# tests/integration/test_bridge_handler_integration/setup_helpers.py
def setup_test_containers_config(
    monkeypatch: pytest.MonkeyPatch,
    kafka_bootstrap: str,
    rabbitmq_url: str,
    exchange: str = "test-events",  # ✅ CONFIGURABLE
    consumer_group_id: str = "eventing-consumers",  # ✅ CONFIGURABLE
) -> tuple[str, str, str]:
    monkeypatch.setenv("KAFKA_BOOTSTRAP_SERVERS", kafka_bootstrap)
    monkeypatch.setenv("RABBITMQ_URL", rabbitmq_url)
    return kafka_bootstrap, rabbitmq_url, consumer_group_id
```

### 3. Tests use unique identifiers

**Modified test**:
```python
# tests/integration/test_bridge_handler_integration/test_idempotency.py
async def test_prevents_duplicate_publishing():
    kafka_bootstrap, rabbitmq_url, consumer_group_id = setup_test_containers_config(
        monkeypatch,
        kafka_container.get_bootstrap_server(),
        rabbit_container.get_connection_url(),
        exchange="test-events-idempotency",  # ✅ UNIQUE
        consumer_group_id="idempotency-test-group",  # ✅ UNIQUE
    )
    
    bridge_config = BridgeConfig(
        kafka_topic="topic",
        rabbitmq_exchange="test-events-idempotency",
        routing_key_template="template",
        consumer_group_id="idempotency-test-group",  # ✅ UNIQUE
    )
```

**Different test**:
```python
# tests/integration/test_bridge_handler_integration/test_exception_nack.py
async def test_handles_exception():
    kafka_bootstrap, rabbitmq_url, consumer_group_id = setup_test_containers_config(
        monkeypatch,
        kafka_container.get_bootstrap_server(),
        rabbit_container.get_connection_url(),
        exchange="test-events-exception-nack",  # ✅ DIFFERENT
        consumer_group_id="exception-nack-test-group",  # ✅ DIFFERENT
    )
```

### 4. Ultimate solution: Unique Kafka topics

Consumer group isolation still insufficient - needed unique topics per test.

**Root cause**: All tests used same Kafka topic "events" even with unique consumer groups. Kafka topics store messages; consumer groups only track offsets. Multiple groups reading same topic see ALL messages.

**Final fix** (commit a8c4f20):

```python
# Each test uses OWN Kafka topic
test_idempotency.py → topic="events-idempotency-test"
test_exception_nack.py → topic="events-exception-nack-test"
test_empty_json.py → topic="events-empty-json-test"

# Setup helper now accepts kafka_topic parameter
def setup_test_containers_config(
    kafka_container,
    rabbitmq_container,
    monkeypatch,
    kafka_topic: str = "events",  # NEW
    exchange: str = "test-events",
    consumer_group_id: str = "test",
) -> tuple[str, str, str]:
    pass

def initialize_production_bridge(
    session_factory,
    consumer_group_id: str = "test",
    kafka_topic: str = "events",  # NEW
) -> tuple[Any, Any]:
    bridge_config = BridgeConfig(
        kafka_topic=kafka_topic,  # Dynamic
        consumer_group_id=consumer_group_id,
    )
```

**Per-test usage**:
```python
# test_idempotency.py
setup_test_containers_config(
    kafka_topic="events-idempotency-test",  # UNIQUE TOPIC
    consumer_group_id="idempotency-test-group",
)
producer.produce("events-idempotency-test", ...)  # Use unique topic

# test_exception_nack.py  
setup_test_containers_config(
    kafka_topic="events-exception-nack-test",  # DIFFERENT TOPIC
    consumer_group_id="exception-nack-test-group",
)
producer.produce("events-exception-nack-test", ...)  # Use unique topic
```

See: `2026-04-13-shared-kafka-topic-cross-contamination-bug.md` for full details.

## Files changed

**Production code**:
1. `src/messaging/infrastructure/pubsub/bridge/config.py` - Added `consumer_group_id` field
2. `src/messaging/main/_initialization/bridge_setup/config.py` - Pass consumer group to config
3. `src/messaging/main/_initialization/bridge_setup/handler_registration.py` - Use config value

**Test code**:
1. `tests/integration/test_bridge_handler_integration/setup_helpers.py` - Accept unique IDs
2. `tests/integration/test_bridge_handler_integration/test_idempotency.py` - Pass unique IDs
3. `tests/integration/test_bridge_handler_integration/test_exception_nack.py` - Pass unique IDs

## Verification

**Before fix**:
```bash
pytest tests/integration/test_bridge_handler_integration/ -v
# FAILED: 7 failures due to cross-contamination
```

**After fix**:
```bash
pytest tests/integration/test_bridge_handler_integration/ -v
# PASSED: All tests isolated
```

## Prevention rules

**Always when writing integration tests**:

1. **Never hardcode infrastructure resource IDs in production code**
   - Consumer groups, queue names, exchange names
   - Database names, table names
   - Cache keys, Redis DBs
   - API endpoints, webhook URLs

2. **Make all resource IDs configurable**
   - Accept via configuration class
   - Default to production values
   - Override in tests with unique per-test values

3. **Setup helpers must accept unique identifiers**
   - Add parameters for all shared resources
   - Use descriptive defaults
   - Return all IDs for test verification

4. **Each test must use unique identifiers**
   - Generate unique names: `f"test-{uuid4()}"`
   - Or use test-specific names: `f"test-{test_name}"`
   - Never use shared/hardcoded names

5. **Verify isolation**
   - Run tests together: `pytest tests/integration/`
   - Run tests in random order: `pytest --random-order`
   - Run tests in parallel: `pytest -n auto`
   - All must pass

## Related issues

- **Kafka consumer group isolation**: See `2026-04-13-kafka-consumer-group-test-isolation-bug.md`
- **Pytest conftest structure**: See `2026-04-13-pytest-conftest-import-path-mismatch-bug.md`
- **Mock decorator ordering**: See `2026-04-13-python-mock-decorator-parameter-ordering-bug.md`

## Impact

**Before**: 7 test failures, CI blocked, flaky tests
**After**: All tests pass, CI green, no flakiness

**Key lesson**: Integration tests MUST have isolation at the infrastructure level, not just at the code level. Shared infrastructure resources are the primary source of test cross-contamination.

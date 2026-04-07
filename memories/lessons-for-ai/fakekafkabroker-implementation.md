# FakeKafkaBroker implementation and contract validation

**[Implementation](#implementation)** • **[Contract test](#contract-test)** • **[Bugs caught](#bugs-caught)**

## Implementation

`FakeKafkaBroker` in `tests/unit/infrastructure/conftest.py` is implemented from FastStream official documentation, NOT by copying the real `KafkaBroker` class.

### Documentation source

```python
class FakeKafkaBroker:
    """Broker fake that records publish arguments.
    
    Signature sourced from FastStream official documentation:
    https://faststream.ag2.ai/latest/api/faststream/kafka/broker/KafkaBroker/
    
    This fake is intentionally NOT copied from the real KafkaBroker import.
    Instead, it's implemented based on official docs, then validated against
    the real implementation by test_fake_broker_contract.py runtime inspection.
    """
```

### Key parameters

From official FastStream documentation:

```python
async def publish(
    self,
    message: dict[str, object],  # We use dict instead of SendableMessage
    *,
    topic: str = "",
    key: bytes | None = None,
    partition: int | None = None,
    timestamp_ms: int | None = None,
    headers: dict[str, str] | None = None,
    correlation_id: str | None = None,
    reply_to: str = "",
    no_confirm: bool = False,
) -> None:
```

**Note**: We intentionally use `dict[str, object]` for message instead of `SendableMessage` as it's more explicit for test purposes.

## Contract test

`test_fake_broker_contract.py` validates that documentation-based implementation matches reality using `inspect.signature()`.

### What it validates

1. **Parameter names** - All params from real class exist in fake
2. **Default values** - Defaults match exactly (e.g., `None`, `""`, `False`)
3. **Type annotations** - Types are equivalent (normalized for comparison)

### No infrastructure needed

Uses `inspect.signature()` to compare Python class definitions at import time:
- ❌ No running Kafka broker
- ❌ No Testcontainers
- ❌ No Docker
- ❌ No network
- ✅ Only FastStream library installed

## Bugs caught

Runtime inspection caught real mismatches during our implementation:

### 1. Missing parameter

```python
# Initial fake (from partial docs)
async def publish(self, message, *, topic, key) -> None:
    ...

# Contract test found
# ❌ Missing: no_confirm, partition, timestamp_ms, headers, correlation_id, reply_to
```

### 2. Wrong default values

```python
# What we initially had (from unclear docs)
correlation_id: str = ""
reply_to: str = ""

# What it actually is (caught by inspection)
correlation_id: str | None = None
reply_to: str = ""
```

### 3. Type annotation differences

Real broker has runtime type objects (`<class 'str'>`), our fake had string annotations (`"str"`). Normalized these for comparison but caught the difference.

## Type safety layer

In `test_kafka_publisher.py`, we add Mypy validation:

```python
async def _test_publish_helper(broker: KafkaBroker) -> None:
    """Helper that accepts real KafkaBroker type for Mypy validation."""
    publisher = KafkaEventPublisher(broker)
    await publisher.publish_to_topic("topic", {"event": "data"})


async def test_kafka_publisher() -> None:
    broker = FakeKafkaBroker()
    await _test_publish_helper(cast(KafkaBroker, broker))  # Mypy checks
```

## Why this approach works

### Avoids circular validation

❌ **Bad**: Copy `KafkaBroker` → Test checks fake matches real → Always passes (circular)

✅ **Good**: Implement from docs → Test checks docs match real → Catches drift

### Catches documentation lag

Official documentation can lag behind code. Runtime inspection catches:
- Parameters added to code but not yet in docs
- Changed defaults not yet documented
- Type changes not yet reflected

### Future-proof

When FastStream updates their API:
1. Contract test fails during `pytest`
2. Check latest docs: https://faststream.ag2.ai/latest/api/faststream/kafka/broker/KafkaBroker/
3. Update `FakeKafkaBroker` to match
4. Verify tests pass

## Files

- `tests/unit/infrastructure/conftest.py` - FakeKafkaBroker implementation
- `tests/unit/infrastructure/test_fake_broker_contract.py` - Contract validation
- `tests/unit/infrastructure/test_kafka_publisher.py` - Type-checked usage
- `docs/testing/test-double-contract-validation.md` - Full documentation

## Related

- Universal lesson: `memories/lessons-for-ai/universal/testing/test-double-contract-validation.md`
- Cursor rule: `.cursor/rules/test-doubles.mdc`

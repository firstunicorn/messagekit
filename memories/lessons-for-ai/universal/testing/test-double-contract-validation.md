# Test double contract validation from documentation

**[Approach](#approach)** • **[Why](#why)** • **[Implementation](#implementation)** • **[Benefits](#benefits)**

## Approach

Test doubles (fakes, mocks) should be implemented from **official documentation**, then validated against real implementation via runtime inspection.

## Why this matters

### The circular validation trap

```python
# ❌ BAD: Circular validation (no value)
1. Copy signature from real class
2. Test checks fake matches real
3. Result: Test always passes because fake was copied from real

# ✅ GOOD: Documentation-based validation (catches drift)
1. Implement fake from official documentation
2. Test checks documentation matches real implementation
3. Result: Test catches doc vs. implementation drift
```

### Real-world benefit

During our implementation, runtime inspection caught:
- Missing parameter `no_confirm` (not in docs)
- Wrong default value for `correlation_id` (docs showed `""`, actual was `None`)
- Type annotation mismatches

**Without runtime validation, these bugs would remain hidden until integration tests failed.**

## Implementation

### Step 1: Source signature from documentation

```python
class FakeKafkaBroker:
    """Broker fake that records publish arguments.
    
    Signature sourced from FastStream official documentation:
    https://faststream.ag2.ai/latest/api/faststream/kafka/broker/KafkaBroker/
    
    This fake is intentionally NOT copied from the real KafkaBroker import.
    Instead, it's implemented based on official docs, then validated against
    the real implementation by test_fake_broker_contract.py runtime inspection.
    """
    
    async def publish(
        self,
        message: dict[str, object],
        *,
        topic: str = "",
        key: bytes | None = None,
        # ... parameters from documentation ...
    ) -> None:
        """Record all publish calls.
        
        Parameters match FastStream KafkaBroker.publish() as documented at:
        https://faststream.ag2.ai/latest/api/faststream/kafka/broker/KafkaBroker/
        """
```

### Step 2: Create contract test with runtime inspection

```python
import inspect
from real_library import RealClass
from tests.conftest import FakeClass


def test_fake_matches_real_signature() -> None:
    """Validate FakeClass stays in sync with RealClass.
    
    This test uses inspect.signature() to compare method signatures.
    No infrastructure needed - only inspects class definitions.
    """
    real_sig = inspect.signature(RealClass.method)
    fake_sig = inspect.signature(FakeClass.method)
    
    # Compare parameter names
    assert set(real_sig.parameters.keys()) == set(fake_sig.parameters.keys())
    
    # Compare defaults and types
    for param_name in real_sig.parameters:
        if param_name == "self":
            continue
            
        real_param = real_sig.parameters[param_name]
        fake_param = fake_sig.parameters[param_name]
        
        assert real_param.default == fake_param.default
        # Compare type annotations...
```

### Step 3: Add type safety with Mypy

```python
# Use real class type in helper for static validation
async def _test_helper(client: RealClass) -> None:
    """Helper that accepts real type for Mypy validation."""
    await client.method(...)


# Tests can cast fake to real type
fake = FakeClass()
await _test_helper(cast(RealClass, fake))
```

## Benefits

| Layer | Purpose | When it catches issues | Infrastructure needed |
|-------|---------|----------------------|----------------------|
| Documentation-based implementation | Authoritative API source | N/A | None |
| Mypy type checking | Static type safety | During development | None |
| Runtime inspection test | Automatic drift detection | During pytest | None |

### No infrastructure dependencies

Runtime inspection requires **zero infrastructure**:
- ❌ No running services (Kafka, databases, etc.)
- ❌ No containers or Docker
- ❌ No network connections
- ✅ Only the library installed for import

### Future-proof

When library updates:
1. Contract test fails during `pytest`
2. Check official docs for changes
3. Update fake to match new signature
4. Verify all tests pass

## When to use

Use this pattern for test doubles of:
- External libraries with evolving APIs
- Third-party services (Kafka, databases, cloud SDKs)
- Any dependency where API changes could break tests silently

## Files

In our implementation:
- `tests/unit/infrastructure/conftest.py` - Documentation-based fake
- `tests/unit/infrastructure/test_fake_broker_contract.py` - Contract validation
- `tests/unit/infrastructure/test_kafka_publisher.py` - Type-checked usage

## Key principle

**Test doubles are documentation artifacts, not code artifacts.**

They should reflect what the API **claims to be** (documentation), validated against what it **actually is** (implementation). This catches the most insidious bugs: documentation drift.

# Test Double Contract Validation - Implementation Summary

**Date:** 2026-04-05  
**Approach:** Documentation-based implementation with runtime validation

## Core principle

**FakeKafkaBroker is implemented from DOCUMENTATION, not by copying code.**

This ensures:
- We follow the documented API (source of truth for users)
- Contract test validates documentation vs. actual implementation
- No circular validation (fake copies real, test checks fake matches real)

## Implementation layers

### Layer 1: Documentation-based implementation
**Source:** FastStream official documentation  
**URL:** https://faststream.ag2.ai/latest/api/faststream/kafka/broker/KafkaBroker/  
**Location:** `tests/unit/infrastructure/conftest.py`

`FakeKafkaBroker.publish()` signature implemented based on:
- Web search for FastStream KafkaBroker documentation
- Official API reference for parameter names, types, defaults
- Documentation explains purpose of each parameter

**Key detail:** We use `dict[str, object]` for message (not `SendableMessage`) as it's more explicit for tests.

### Layer 2: Static type checking (Mypy)
**Purpose:** Development-time type safety  
**Location:** `tests/unit/infrastructure/test_kafka_publisher.py`

- Imports real `KafkaBroker` class for type annotations
- Helper function `_test_publish_helper(broker: KafkaBroker)` validates compatibility
- Mypy catches type mismatches before commit
- No runtime overhead, pure static analysis

### Layer 3: Runtime signature inspection (Contract test)
**Purpose:** Automatic validation that documentation matches reality  
**Location:** `tests/unit/infrastructure/test_fake_broker_contract.py`

- Uses `inspect.signature()` to compare method signatures
- Validates: parameter names, defaults, type annotations
- **No Kafka instance needed** - inspects class definitions only
- Catches drift between documentation and implementation

## Real bugs caught

The contract test caught mismatches during implementation that web docs didn't show:

1. **Missing parameter:** `no_confirm: bool = False` - existed in code, not in initial docs
2. **Wrong defaults:** `correlation_id` was documented as `""`, actual default is `None`
3. **Type differences:** Runtime uses `types.UnionType`, string annotations differ

**These bugs prove the value of runtime validation** - even authoritative documentation can lag behind code.

## Why this approach works

| Approach | Problem |
|----------|---------|
| ❌ Copy real class | Circular: fake copies real, test checks copy matches real (no value) |
| ❌ Manual only | Human error, missed parameters, doc lags behind code |
| ✅ Docs + validation | Authoritative source + automatic verification of accuracy |

## Benefits

- **Authoritative:** Based on what users read (documentation)
- **Automatic:** Contract test catches doc vs. code drift
- **No infrastructure:** Works without running Kafka
- **Future-proof:** Detects API changes immediately
- **Type-safe:** Mypy validates at development time

## Files modified

- `tests/unit/infrastructure/conftest.py` - Documentation-based `FakeKafkaBroker`
- `tests/unit/infrastructure/test_kafka_publisher.py` - Type-checked helper function
- `tests/unit/infrastructure/test_fake_broker_contract.py` - Runtime contract validation

## When contract test fails

1. FastStream updated their API (added/removed/renamed parameter)
2. Check official docs: https://faststream.ag2.ai/latest/api/faststream/kafka/broker/KafkaBroker/
3. Update `FakeKafkaBroker` to match new signature
4. Run tests to verify compatibility
5. Document any intentional differences (e.g., stricter types)

## Recommendation

**Use this pattern for all test doubles of external libraries with evolving APIs.**

The combination of documentation-based implementation + runtime validation provides the best of both worlds:
- Follow official API (what users expect)
- Catch implementation drift automatically
- No circular validation
- No infrastructure dependencies

# Testing Documentation

**[Strategy](#strategy)** • **[Unit Patterns](#unit-test-patterns)** • **[Integration Patterns](#integration-test-patterns)**

## Strategy

### Coverage Targets
**File:** [strategy/coverage-strategy.md](./strategy/coverage-strategy.md)

- Overall: 80% coverage (pytest --cov-fail-under=80)
- Critical paths: 85% minimum (circuit breaker, idempotency store, publishers)
- Risk-based approach with tiered thresholds

---

## Unit Test Patterns

### Test Double Contract Validation
**File:** [patterns/unit/test-double-contract-validation.md](./patterns/unit/test-double-contract-validation.md)

Pattern for creating test doubles (fakes, mocks) with automatic contract validation:

1. **Implement from documentation** (not by copying real class)
2. **Add contract test** using `inspect.signature()`
3. **Validate with Mypy** via type-checking helper

**Example:** `FakeKafkaBroker` implemented from FastStream docs, validated against real `KafkaBroker` signature.

---

## Integration Test Patterns

### Setup Patterns
**File:** [patterns/integration/setup-patterns.md](./patterns/integration/setup-patterns.md)

How to write integration tests using Testcontainers (Kafka, RabbitMQ):

- Setup helper functions for container configuration
- Required pytest fixtures (containers, database, monkeypatch)
- Timing considerations (sleeps, waits)
- Test structure and markers

**Critical:** Every test MUST use unique infrastructure identifiers.

### Isolation Architecture
**File:** [patterns/integration/isolation-architecture.md](./patterns/integration/isolation-architecture.md)

Root cause analysis of test cross-contamination:

**Problem:** Shared Kafka topics + shared consumer groups = message leakage between tests

**Solution:**
- Unique Kafka topic per test
- Unique consumer group ID per test
- Unique RabbitMQ exchange/queue per test

**Pattern:**
```python
kafka_topic = f"events-{test_name}-{uuid4()}"
consumer_group = f"{test_name}-group-{uuid4()}"
```

---

## Quick Links

| Category | Document | Purpose |
|----------|----------|---------|
| Strategy | [Coverage](./strategy/coverage-strategy.md) | Thresholds and rationale |
| Unit | [Test Doubles](./patterns/unit/test-double-contract-validation.md) | Fake implementation pattern |
| Integration | [Setup](./patterns/integration/setup-patterns.md) | Container configuration |
| Integration | [Isolation](./patterns/integration/isolation-architecture.md) | Prevent cross-contamination |

---

## Testing Philosophy

1. **Risk-based coverage** - Critical paths (85%) get more testing than config (80%)
2. **Documentation-driven fakes** - Implement from docs, validate with runtime checks
3. **Infrastructure isolation** - Unique IDs prevent test interference
4. **Under 100 lines** - Split large test files into sub-folders
5. **Fast unit, slow integration** - Unit tests use fakes, integration uses Testcontainers

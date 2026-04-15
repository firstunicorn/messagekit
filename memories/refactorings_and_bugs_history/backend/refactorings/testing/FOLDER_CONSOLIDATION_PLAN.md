# Documentation Folder Consolidation Plan

## Current state (confusing)

```
docs/
├── testing/                          # "Methodology" documentation
│   ├── coverage-strategy.md
│   └── test-double-contract-validation.md
│
└── tests/                            # "Implementation" documentation
    ├── integration-test-setup-patterns.md
    └── test-isolation-architecture.md
```

**Problem:** Overlap in purpose, unclear distinction between folders.

---

## Proposed structure (clear)

```
docs/
└── testing/
    ├── README.md                     # Testing overview and index
    │
    ├── strategy/
    │   └── coverage-strategy.md      # Coverage thresholds (80% overall, 85% critical)
    │
    └── patterns/
        ├── unit/
        │   └── test-double-contract-validation.md  # Fake implementation pattern
        │
        └── integration/
            ├── setup-patterns.md                   # How to write integration tests
            └── isolation-architecture.md           # Root cause analysis of cross-contamination
```

---

## Migration steps

1. **Create new structure:**
   ```powershell
   cd "c:\coding\gridflow-microservices-codex-taskmaster\microservices\eventing"
   mkdir docs\testing\strategy
   mkdir docs\testing\patterns\unit
   mkdir docs\testing\patterns\integration
   ```

2. **Move files:**
   ```powershell
   # Move strategy
   move docs\testing\coverage-strategy.md docs\testing\strategy\
   
   # Move unit test patterns
   move docs\testing\test-double-contract-validation.md docs\testing\patterns\unit\
   
   # Move integration test patterns
   move docs\tests\integration-test-setup-patterns.md docs\testing\patterns\integration\setup-patterns.md
   move docs\tests\test-isolation-architecture.md docs\testing\patterns\integration\isolation-architecture.md
   ```

3. **Create index (README.md):**
   See content below.

4. **Remove old folder:**
   ```powershell
   rmdir docs\tests  # Should be empty now
   ```

5. **Update references:**
   Search codebase for references to old paths:
   ```powershell
   rg "docs/tests/" --type md
   rg "docs/testing/" --type md
   ```

---

## New README.md

**File:** `docs/testing/README.md`

```markdown
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
```

---

## Benefits of consolidation

1. **Single source of truth** - All testing docs in one place
2. **Clear hierarchy** - Strategy → Patterns → Unit/Integration
3. **Easier navigation** - Index file shows all options
4. **Less confusion** - No "testing vs tests" ambiguity
5. **Scales better** - Easy to add new patterns (e2e, property-based, chaos)

---

## Alternative: Keep both but clarify

If you prefer to keep both folders, rename them:

```
docs/
├── testing-strategy/         # Methodology, coverage, philosophy
└── testing-patterns/         # Implementation guides (unit, integration)
```

But consolidation is cleaner.

# Test isolation principles

**[Rule](#rule)** • **[Requirements](#requirements)** • **[Patterns](#patterns)**

## Rule

Tests MUST be isolated. Each test must run independently without affecting or being affected by other tests.

## Critical requirements

**Every shared resource MUST have unique identifier per test**:

### Infrastructure resources
- Database names, schemas, tables
- Message queue topics, exchanges, queues
- Consumer groups, subscription IDs
- Cache keys, Redis databases
- File paths, temp directories
- Network ports, socket addresses
- API endpoints, webhook URLs

### Application state
- User accounts, session IDs
- Transaction IDs, request IDs
- Configuration overrides
- Environment variables
- Global singletons, registries

## Why tests fail without isolation

**Shared state causes cross-contamination**:

```
Test A runs:
  - Creates record with ID "test-user"
  - Asserts count == 1
  
Test B runs (shares same DB):
  - Queries all records
  - Finds Test A's record still present
  - Asserts count == 1
  - FAILS: count == 2
```

**Timing dependencies break in CI**:
- Local: Tests run sequentially, appear to work
- CI: Tests run in parallel or different order
- Shared resources cause race conditions
- Flaky tests that "sometimes" pass

## Implementation patterns

### Pattern 1: Unique identifiers per test

```python
# WRONG - Hardcoded shared identifier
def test_create_user():
    user = create_user(username="testuser")  # Shared name
    assert user.username == "testuser"

# CORRECT - Unique per test run
from uuid import uuid4

def test_create_user():
    username = f"testuser-{uuid4()}"  # Unique
    user = create_user(username=username)
    assert user.username == username
```

### Pattern 2: Configurable resource IDs

```python
# WRONG - Hardcoded in production code
@broker.subscriber(
    "my-topic",
    group_id="my-app-consumers"  # Hardcoded
)

# CORRECT - Configurable
@broker.subscriber(
    config.topic,
    group_id=config.consumer_group_id  # From config
)

# Test usage
def test_consumer():
    config = Config(
        topic="my-topic",
        consumer_group_id=f"test-{uuid4()}"  # Unique
    )
```

### Pattern 3: Scoped fixtures

```python
# Session-scoped for expensive resources
@pytest.fixture(scope="session")
def database_container():
    """Shared container, but each test gets unique DB."""
    with PostgresContainer() as container:
        yield container

# Function-scoped for test isolation
@pytest.fixture(scope="function")
def database_session(database_container):
    """Unique DB session per test."""
    db_name = f"test_{uuid4()}"
    engine = create_engine(f"{database_container.url}/{db_name}")
    yield engine
    # Cleanup happens automatically
```

### Pattern 4: Setup helpers with isolation

```python
def setup_test_infrastructure(
    container,
    monkeypatch,
    # REQUIRED: Allow unique IDs per test
    consumer_group: str = f"test-{uuid4()}",
    exchange: str = f"test-exchange-{uuid4()}",
    queue: str = f"test-queue-{uuid4()}",
) -> tuple[str, str, str, str]:
    """Setup with UNIQUE identifiers.
    
    Returns all IDs for verification.
    """
    url = container.get_connection_url()
    monkeypatch.setattr(settings, "broker_url", url)
    
    return url, consumer_group, exchange, queue
```

## Prevention checklist

Before writing integration test:
- [ ] All infrastructure IDs unique per test run
- [ ] No hardcoded resource identifiers in production code
- [ ] Setup helpers accept configurable IDs
- [ ] Fixtures properly scoped (session vs function)
- [ ] Test doesn't assume clean initial state
- [ ] Test doesn't rely on execution order
- [ ] Cleanup happens in teardown or fixture exit

## Common isolation violations

**1. Shared database without cleanup**
```python
# BAD
def test_create(): db.insert("users", {"id": 1})
def test_read(): assert db.count("users") == 1  # FAILS if test_create ran first
```

**2. Hardcoded consumer groups**
```python
# BAD
@subscriber("topic", group_id="my-app")  # All tests share same group
```

**3. Shared temporary files**
```python
# BAD
def test_write(): write_file("/tmp/test.txt", data)
def test_read(): assert read_file("/tmp/test.txt")  # Depends on test_write
```

**4. Global state mutation**
```python
# BAD
def test_configure(): os.environ["MODE"] = "test"
def test_production(): assert os.environ["MODE"] == "prod"  # FAILS
```

## Error symptoms indicating lack of isolation

- `AssertionError: assert 1 == 2` (unexpected count)
- `AssertionError: assert [] == [item]` (unexpected existing data)
- Flaky tests (pass/fail randomly)
- Tests pass locally, fail in CI
- Tests fail when run together, pass when run solo
- Different results based on test execution order

## Verification

**Test isolation is correct when**:
1. Tests pass in any execution order
2. Tests pass when run solo: `pytest tests/test_specific.py::test_one`
3. Tests pass when run together: `pytest tests/`
4. Tests pass in parallel: `pytest -n auto`
5. No test assumes clean state from previous test
6. No test leaves state that affects next test

**Run this to verify**:
```bash
# Run tests in random order
pytest --random-order

# Run specific test solo
pytest path/to/test.py::test_specific -v

# Run all tests in parallel
pytest -n auto

# All should pass if properly isolated
```

## Universal principle

**Every test is an independent experiment**. Treat shared resources like chemistry lab equipment - clean before and after use, never assume previous experiment cleaned up properly.

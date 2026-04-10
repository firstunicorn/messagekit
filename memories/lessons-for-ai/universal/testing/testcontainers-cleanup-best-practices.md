# Testcontainers cleanup best practices

**Problem:** Orphaned Docker containers from failed/interrupted test runs accumulate, causing:
- Port conflicts (container still bound to port)
- Resource exhaustion (memory, disk)
- Flaky tests (connecting to stale container)
- Slow CI (Docker daemon overhead)

## Two-phase cleanup strategy

**Critical:** Stop containers first, then remove. Immediate removal can fail if container is still running.

```python
def pytest_sessionstart(session: pytest.Session) -> None:
    """Cleanup testcontainers BEFORE tests start."""
    import subprocess
    import time
    
    # Find all testcontainers (safe - labeled containers only)
    result = subprocess.run(
        ["docker", "ps", "-a", "-q", "--filter", "label=org.testcontainers=true"],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    
    if result.returncode != 0:
        return
        
    container_ids = [cid.strip() for cid in result.stdout.strip().split("\n") if cid.strip()]
    
    if container_ids:
        # Phase 1: Stop running containers
        subprocess.run(
            ["docker", "stop", *container_ids],
            capture_output=True,
            timeout=30,
            check=False,
        )
        
        # Wait for containers to fully stop
        time.sleep(2)
        
        # Phase 2: Remove stopped containers
        subprocess.run(
            ["docker", "rm", *container_ids],
            capture_output=True,
            timeout=30,
            check=False,
        )
        
        # Wait for Docker daemon to stabilize
        time.sleep(5)
```

**Why two-phase:**
- `docker rm` on running container requires `-f` (force) which can corrupt data
- Graceful stop lets containers clean up properly
- 2-second delay ensures stop completes before remove
- 5-second final delay prevents immediate test start overwhelming Docker daemon

## Safety via label filtering

**Never** use `docker ps -a -q` without filters - will target all containers.

**Always** filter by testcontainers label:
```bash
--filter "label=org.testcontainers=true"
```

Testcontainers automatically adds this label. Safe to cleanup aggressively.

## When to cleanup

### Before tests (sessionstart)
Clears stale containers from previous runs. Prevents port conflicts and resource issues.

```python
def pytest_sessionstart(session: pytest.Session) -> None:
    """Cleanup BEFORE tests start."""
    # ... cleanup code
```

### After tests (sessionfinish)
Ensures clean state even if tests interrupted (Ctrl+C, timeout, crash).

```python
def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Cleanup after ALL tests complete or are interrupted."""
    # ... same cleanup code
```

**Critical:** Use `sessionfinish` not `sessionclose`. `sessionfinish` runs even on interruption.

## Handling cleanup failures

```python
try:
    # cleanup code
except subprocess.TimeoutExpired:
    logger.warning("Docker cleanup timed out - Docker daemon may be slow")
except Exception as e:
    logger.debug("Cleanup skipped", error=str(e))
    # Don't fail tests due to cleanup issues
```

**Never** fail tests because cleanup fails. Cleanup is best-effort hygiene.

## Common mistakes

### Mistake 1: Using `docker ps` without `-a`
```python
# ❌ Wrong - only finds running containers
subprocess.run(["docker", "ps", "-q", "--filter", "label=org.testcontainers=true"])

# ✅ Correct - finds all containers (running and stopped)
subprocess.run(["docker", "ps", "-a", "-q", "--filter", "label=org.testcontainers=true"])
```

### Mistake 2: Immediate remove without stop
```python
# ❌ Wrong - can fail if container still running
subprocess.run(["docker", "rm", "-f", *container_ids])

# ✅ Correct - stop first, then remove
subprocess.run(["docker", "stop", *container_ids])
time.sleep(2)
subprocess.run(["docker", "rm", *container_ids])
```

### Mistake 3: No delay between operations
```python
# ❌ Wrong - Docker daemon may not finish stop before remove
subprocess.run(["docker", "stop", *container_ids])
subprocess.run(["docker", "rm", *container_ids])  # May fail

# ✅ Correct - wait for operations to complete
subprocess.run(["docker", "stop", *container_ids])
time.sleep(2)  # Let stop finish
subprocess.run(["docker", "rm", *container_ids])
time.sleep(5)  # Let Docker daemon stabilize
```

### Mistake 4: Not using timeout
```python
# ❌ Wrong - can hang indefinitely if Docker daemon stuck
subprocess.run(["docker", "ps", "-a", "-q"])

# ✅ Correct - timeout prevents hanging tests
subprocess.run(["docker", "ps", "-a", "-q"], timeout=10)
```

## CI-specific considerations

CI environments often have slower Docker daemons. Increase delays:

```python
# Local development
time.sleep(2)  # stop → remove
time.sleep(5)  # stabilization

# CI environment
time.sleep(5)  # stop → remove
time.sleep(10)  # stabilization
```

Detect CI via environment variables:
```python
is_ci = os.getenv("CI") == "true" or os.getenv("GITHUB_ACTIONS") == "true"
delay = 5 if is_ci else 2
```

## Session-scoped fixtures

Use session scope for expensive containers (Kafka, PostgreSQL, RabbitMQ):

```python
@pytest.fixture(scope="session")
def kafka_container(docker_or_skip):
    """Reuse container across all tests in session."""
    kafka = KafkaContainer("confluentinc/cp-kafka:7.6.1")
    with kafka:
        yield kafka
    # Container auto-removed by context manager
```

**Benefits:**
- Single container for all tests (faster)
- Automatic cleanup via context manager
- Startup cost amortized across tests

**Trade-off:** Tests share state. Ensure proper cleanup between tests (delete topics, flush data).

## Monitoring cleanup effectiveness

Log cleanup to verify it's working:

```python
import structlog

logger = structlog.get_logger()

if container_ids:
    logger.info(
        "Cleaning testcontainers",
        count=len(container_ids),
        container_ids=container_ids[:5],  # Log first 5 for debugging
    )
    # ... cleanup
    logger.info("Testcontainers cleanup complete", removed=len(container_ids))
```

Check logs after test runs - should see cleanup messages with 0 containers if clean state achieved.

## Windows-specific notes

Windows Docker Desktop slower than Linux. Increase timeouts:

```python
# Windows needs longer timeouts
DOCKER_TIMEOUT = 30  # vs 10 on Linux
STOP_DELAY = 3       # vs 2 on Linux
STABILIZE_DELAY = 10 # vs 5 on Linux
```

Windows path issues - use subprocess instead of shell commands to avoid path escaping.

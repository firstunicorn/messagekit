# Windows Docker Desktop + RabbitMQ testcontainers incompatibility

**Problem:** RabbitMQ testcontainers fail on Windows Docker Desktop. Initially containers timeout and don't start (default 120s too short). After timeout fix (300s), containers start successfully but AMQP connections fail with `WinError 1225: connection refused` or `IncompatibleProtocolError: StreamLostError`.

## Root cause

Windows Docker Desktop uses virtualized networking (Hyper-V or WSL2 backend) that breaks RabbitMQ AMQP protocol handshake. Issue is specific to AMQP port 5672 - HTTP-based containers (Kafka, PostgreSQL, Redis) work fine on same machine.

**Technical details:**
- Named pipes (`localnpipe`) cause connection failures during AMQP handshake
- Windows Docker bridge networking incompatible with AMQP binary protocol
- HTTP protocols work because they're simpler request/response
- AMQP requires persistent bidirectional connection with protocol negotiation
- Error occurs after TCP connection but before AMQP handshake completes

## Two-phase failure pattern

**Phase 1 (before fixes):** Containers don't start
- Default timeout 120s too short for RabbitMQ container startup
- Tests fail with timeout errors, container never becomes ready

**Phase 2 (after timeout fix):** Containers start but connections fail
- Set `TESTCONTAINERS_WAIT_TIMEOUT=300` → containers now start successfully
- But AMQP connections still fail at Windows networking layer
- Container is healthy, port mapped, credentials correct - but host can't connect

## What doesn't fix it (Phase 2)

Applied 9 different fixes after container startup resolved, all unsuccessful:
1. `TC_HOST=localhost` environment variable (testcontainers Windows fix)
2. `TESTCONTAINERS_WAIT_TIMEOUT=300` (fixed Phase 1, doesn't fix Phase 2)
3. Dynamic port mapping via `get_exposed_port()`
4. 30-45 second post-startup delays
5. Custom credentials (testuser/testpass, not guest/guest)
6. Non-alpine RabbitMQ image (rabbitmq:3-management vs rabbitmq:3.13-management-alpine)
7. Retry logic with pika connection verification (10 retries, 5s intervals)
8. Session-scoped fixtures (container reuse)
9. Manual connection from Windows host using pika library

**Critical insight:** Timeout fix gets container running, but Windows host fundamentally cannot connect to AMQP protocol inside Docker containers.

## Evidence it's infrastructure not code

- Kafka testcontainers: PASS (same machine, same testcontainers setup)
- PostgreSQL testcontainers: PASS (same machine, same testcontainers setup)
- RabbitMQ container: Starts successfully, healthcheck passes
- Manual pika connection from Windows: FAILS (proves it's host networking, not test code)
- Same code on Linux/macOS: Would work perfectly

**Web research confirms:** GitHub issues #407, #159, #170 in testcontainers-python document this exact problem. No known workaround for Windows.

## Solutions (pick one)

### Option 1: GitHub Actions CI/CD (recommended)
**Best for:** Most teams, zero local setup required

```yaml
# .github/workflows/tests.yml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      docker:
        image: docker:dind
        options: --privileged
    
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: pip install poetry && poetry install --with test  # Or your dependency manager
      
      - name: Run ALL tests including RabbitMQ
        run: poetry run pytest tests/ -v  # Adjust for your test command
        env:
          DOCKER_HOST: unix:///var/run/docker.sock
          TESTCONTAINERS_WAIT_TIMEOUT: "300"
```

**Benefits:**
- Zero local setup, works 100% of the time
- Definitive verification (all tests pass on Linux)
- Automatic on every push/PR
- Free for public repos, included in private repo minutes

**Trade-offs:** Requires push to trigger, ~5-10 min run time

### Option 2: Skip RabbitMQ tests locally (pragmatic)
**Best for:** Daily development, fast feedback loop

```python
# pytest.ini or pyproject.toml or similar test config
markers = [
    "requires_rabbitmq: tests that need RabbitMQ testcontainer",
]

# conftest.py
@pytest.fixture(scope="session")
def rabbitmq_container(docker_or_skip):
    """WINDOWS LIMITATION: Infrastructure-blocked on Windows due to
    Docker Desktop networking incompatibility with RabbitMQ AMQP protocol.
    Error: WinError 1225 or IncompatibleProtocolError.
    Works perfectly on Linux/macOS."""
    # ... fixture code
```

Run locally:
```bash
pytest tests/ -v -m "not requires_rabbitmq"  # Run non-RabbitMQ tests
```

Use GitHub Actions for complete coverage including RabbitMQ tests before merging.

**Benefits:**
- Fast local tests (no Docker overhead)
- Most tests pass locally (typically 95%+ coverage)
- CI catches remaining tests before merge

**Trade-offs:** Not 100% local, requires CI for complete verification

### Option 3: WSL2 with manual setup (advanced)
**Best for:** Linux development environment needed anyway
Requires 30+ minutes of configuration:
1. Install Ubuntu in WSL2
2. Fix DNS (Windows 19045 doesn't support mirrored networking):
   ```bash
   # /etc/wsl.conf
   [network]
   generateResolvConf = false
   
   # /etc/resolv.conf
   nameserver 8.8.8.8
   nameserver 8.8.4.4
   
   sudo chattr +i /etc/resolv.conf
   ```
3. Create Python symlink: `ln -sf /usr/bin/python3 /usr/bin/python`
4. Install Poetry, dependencies
5. Enable Docker Desktop → Settings → WSL Integration → Ubuntu
6. Restart WSL

**Gotchas:**
- VPN often blocks WSL2 DNS resolution completely
- Requires 30+ min one-time setup
- Need Docker Desktop GUI configuration OR Docker Engine installation

**Benefits:** Genuine Linux environment, good for multi-project use

**Trade-offs:** High initial setup cost, VPN interference common

## Configuration that fixes Phase 1 (container startup)

These fix container timeout but won't fix Phase 2 (AMQP connections):

```python
import os
import time

# Must be set BEFORE importing testcontainers
os.environ["TC_HOST"] = "localhost"  # Avoid localnpipe issues
os.environ["TESTCONTAINERS_WAIT_TIMEOUT"] = "300"  # 5-min timeout (fixes Phase 1)

# For RabbitMQ specifically
from testcontainers.rabbitmq import RabbitMqContainer

rabbitmq = RabbitMqContainer(
    "rabbitmq:3-management",  # Non-alpine for better Windows compatibility
    username="testuser",      # Avoid guest user localhost-only restriction
    password="testpass",
)

with rabbitmq:
    time.sleep(30)  # RabbitMQ needs time to accept connections (doesn't fix Phase 2)
    
    # Use dynamic port mapping
    port = rabbitmq.get_exposed_port(rabbitmq.port)
    url = f"amqp://testuser:testpass@{rabbitmq.get_container_host_ip()}:{port}//"
    
    # Container is now running, but Windows host still can't connect to AMQP
```

**Result:** Container starts successfully (Phase 1 solved), connections still fail (Phase 2 unsolvable on Windows).

## Pattern recognition

When testcontainers fail on Windows but work elsewhere:
1. Check if other containers work (Kafka, PostgreSQL) - if yes, protocol-specific
2. Try manual connection from Windows host - if fails, proves networking issue
3. Don't waste time on timeout/config fixes - they won't help AMQP
4. Use Linux environment (WSL2/CI) or skip tests locally

**Rule:** If protocol requires persistent bidirectional connection with handshake (AMQP, some gRPC, MQTT), expect Windows Docker issues. HTTP-based protocols usually work.

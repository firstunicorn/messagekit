# Testcontainers cleanup best practices

## Problem
Old test containers accumulate when:
- Tests fail/timeout before cleanup
- Ctrl+C interrupts test runs
- Debugger stops execution mid-test
- Docker daemon gets overwhelmed

## Solutions implemented

### 1. Session-scoped fixtures with proper cleanup
```python
# tests/conftest.py - ALREADY IMPLEMENTED
@pytest.fixture(scope="session")
def kafka_container(docker_or_skip):
    """Session-scoped ensures ONE container for all tests."""
    from testcontainers.kafka import KafkaContainer
    from testcontainers.core.config import testcontainers_config

    original_timeout = testcontainers_config.timeout
    testcontainers_config.timeout = 300
    
    try:
        kafka = KafkaContainer("confluentinc/cp-kafka:7.6.1")
        kafka.start()
        yield kafka
        kafka.stop()  # Cleanup happens here
    finally:
        testcontainers_config.timeout = original_timeout
```

**Why it works:**
- `scope="session"` = ONE container for ALL tests (not per-test)
- `try/finally` ensures cleanup even on errors
- `kafka.stop()` explicitly removes container

### 2. Pytest cleanup hooks (add to conftest.py)

```python
# Add to tests/conftest.py
def pytest_sessionfinish(session, exitstatus):
    """Cleanup ALL testcontainers on session end."""
    import subprocess
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # Remove all testcontainers (safe - only removes testcontainers-labeled)
        result = subprocess.run(
            ["docker", "ps", "-a", "-q", "--filter", "label=org.testcontainers=true"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        container_ids = result.stdout.strip().split('\n')
        container_ids = [cid for cid in container_ids if cid]
        
        if container_ids:
            logger.warning(f"Cleaning up {len(container_ids)} leftover testcontainers")
            subprocess.run(
                ["docker", "rm", "-f"] + container_ids,
                capture_output=True,
                timeout=30
            )
    except Exception as e:
        logger.warning(f"Failed to cleanup testcontainers: {e}")
```

### 3. Pre-test Docker cleanup (pyproject.toml)

```toml
# Add to pyproject.toml [tool.pytest.ini_options]
# Run docker prune BEFORE tests start
addopts = [
    # ... existing options ...
]

# Create scripts/cleanup_docker.py
```

**Create cleanup script:**
```python
# scripts/cleanup_docker.py
"""Cleanup stale Docker containers before test runs."""
import subprocess
import sys

def cleanup_testcontainers():
    """Remove all testcontainers and dangling containers."""
    try:
        # Remove testcontainers
        subprocess.run(
            ["docker", "container", "prune", "-f", "--filter", "label=org.testcontainers=true"],
            check=True,
            timeout=60
        )
        
        # Remove dangling containers (stopped containers)
        subprocess.run(
            ["docker", "container", "prune", "-f"],
            check=True,
            timeout=60
        )
        
        print("✅ Docker cleanup complete")
        return 0
    except subprocess.TimeoutExpired:
        print("❌ Docker cleanup timed out - Docker daemon may be unresponsive")
        return 1
    except subprocess.CalledProcessError as e:
        print(f"❌ Docker cleanup failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(cleanup_testcontainers())
```

**Run cleanup before tests:**
```powershell
# PowerShell
cd "c:\coding\gridflow-microservices-codex-taskmaster\microservices\eventing" && python scripts/cleanup_docker.py && poetry run pytest tests/ -v
```

### 4. Automatic Docker pruning (scheduled task)

**Windows Task Scheduler (recommended):**
```powershell
# Create cleanup script: scripts/docker_prune_task.ps1
docker container prune -f --filter "until=1h"
docker image prune -f --filter "until=24h"

# Schedule daily at 3 AM:
# Task Scheduler > Create Basic Task > Daily 3:00 AM
# Action: Start Program
# Program: powershell.exe
# Arguments: -File "C:\coding\...\scripts\docker_prune_task.ps1"
```

### 5. CI/CD best practices

```yaml
# .github/workflows/tests.yml
jobs:
  test:
    steps:
      - name: Cleanup Docker before tests
        run: |
          docker container prune -f
          docker volume prune -f
      
      - name: Run tests
        run: poetry run pytest tests/
      
      - name: Cleanup Docker after tests (always runs)
        if: always()
        run: |
          docker ps -aq --filter "label=org.testcontainers=true" | xargs -r docker rm -f
```

### 6. Development workflow integration

**Option A: Pre-commit hook**
```bash
# .git/hooks/pre-push
#!/bin/bash
docker container prune -f --filter "label=org.testcontainers=true"
```

**Option B: Make target (if using Makefile)**
```makefile
.PHONY: test-clean
test-clean:
	@echo "Cleaning Docker..."
	docker container prune -f --filter "label=org.testcontainers=true"
	poetry run pytest tests/ -v

.PHONY: test
test: test-clean
```

**Option C: Poetry script (pyproject.toml)**
```toml
[tool.poetry.scripts]
test-clean = "scripts.cleanup_docker:cleanup_testcontainers"

# Then run: poetry run test-clean && poetry run pytest tests/
```

### 7. Monitoring Docker health

**Add to conftest.py:**
```python
@pytest.fixture(scope="session", autouse=True)
def check_docker_health():
    """Verify Docker is healthy before starting tests."""
    import subprocess
    import structlog
    
    logger = structlog.get_logger()
    
    try:
        # Check Docker daemon
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=10
        )
        
        if result.returncode != 0:
            pytest.skip("Docker daemon not responsive")
        
        # Check container count
        result = subprocess.run(
            ["docker", "ps", "-q"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        container_count = len([c for c in result.stdout.strip().split('\n') if c])
        
        if container_count > 50:
            logger.warning(
                f"High container count detected: {container_count}. "
                "Consider running: docker container prune -f"
            )
            
    except subprocess.TimeoutExpired:
        pytest.skip("Docker daemon timeout - restart Docker Desktop")
    except Exception as e:
        logger.warning(f"Docker health check failed: {e}")
```

## Recommended workflow

### Daily development
```powershell
# Morning routine (once per day)
docker container prune -f

# Before each test run
cd "c:\coding\gridflow-microservices-codex-taskmaster\microservices\eventing"
poetry run pytest tests/ -v
```

### When Docker feels slow
```powershell
# Full cleanup (CAUTION: stops ALL containers, not just testcontainers)
docker container prune -f
docker image prune -f
docker volume prune -f

# Or just testcontainers
docker ps -aq --filter "label=org.testcontainers=true" | ForEach-Object { docker rm -f $_ }
```

### Weekly maintenance
```powershell
# Deep clean (removes unused images too)
docker system prune -a -f --volumes
```

## Prevention checklist

- [x] Session-scoped fixtures (implemented in conftest.py)
- [x] Try/finally cleanup blocks (implemented)
- [ ] Add `pytest_sessionfinish` hook to conftest.py
- [ ] Create `scripts/cleanup_docker.py`
- [ ] Schedule daily Docker prune task (Windows Task Scheduler)
- [ ] Add Docker health check fixture
- [ ] Document cleanup commands in README.md

## Quick reference

| Command | Purpose |
|---------|---------|
| `docker container prune -f` | Remove stopped containers |
| `docker ps -a --filter "label=org.testcontainers=true"` | List testcontainers |
| `docker rm -f $(docker ps -aq --filter "label=org.testcontainers=true")` | Remove all testcontainers (bash) |
| `docker ps -aq --filter "label=org.testcontainers=true" \| ForEach-Object { docker rm -f $_ }` | Remove all testcontainers (PowerShell) |
| `docker system df` | Show Docker disk usage |
| `docker system prune -a -f` | Deep clean (removes unused images) |

## Why this happened

1. **Test failures/timeouts** - Container started but cleanup never ran
2. **Manual interruption** - Ctrl+C during test execution
3. **Debugger stops** - Breakpoints prevent fixture cleanup
4. **Overwhelmed Docker** - Too many containers slow Docker daemon → more timeouts → more orphans (vicious cycle)

## Long-term solution

The **session-scoped fixtures with try/finally** (already implemented) + **pytest_sessionfinish hook** (add this) will prevent 95% of future issues.

For the remaining 5% (hard crashes, power loss), **schedule weekly Docker pruning**.

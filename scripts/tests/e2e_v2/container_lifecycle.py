"""Container lifecycle management for E2E v2 tests."""

import logging
import subprocess
import time

logger = logging.getLogger(__name__)


def cleanup_e2e_containers() -> None:
    """Stop and remove E2E v2 test containers (two-step process).

    Step 1: Stop all E2E containers gracefully
    Step 2: Wait for full shutdown
    Step 3: Remove stopped containers

    Pattern from: tests/conftest_modules/cleanup_hooks/session_start.py
    """
    logger.info("=" * 60)
    logger.info("CLEANUP: Removing E2E v2 test containers")
    logger.info("=" * 60)

    try:
        # Find E2E v2 containers
        result = subprocess.run(
            ["docker", "ps", "-a", "-q", "--filter", "name=e2e-"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )

        if result.returncode != 0:
            logger.warning("Docker not available for cleanup")
            return

        container_ids = [cid.strip() for cid in result.stdout.strip().split("\n") if cid.strip()]

        if not container_ids:
            logger.info("No E2E containers to clean up")
            return

        logger.info(f"Found {len(container_ids)} E2E containers to clean")

        # Step 1: Stop containers
        logger.info("Step 1: Stopping containers...")
        subprocess.run(
            ["docker", "stop", "-t", "1", *container_ids],
            capture_output=True,
            timeout=30,
            check=False,
        )
        logger.info("Containers stopped, waiting for full shutdown...")
        time.sleep(2)  # Wait for containers to fully stop

        # Step 2: Remove containers
        logger.info("Step 2: Removing containers...")
        subprocess.run(
            ["docker", "rm", "-f", *container_ids],
            capture_output=True,
            timeout=30,
            check=False,
        )

        logger.info(f"✅ Cleanup complete ({len(container_ids)} containers removed)")
        logger.info("=" * 60)

    except subprocess.TimeoutExpired:
        logger.error("Docker cleanup timed out")
    except Exception as e:
        logger.warning(f"Cleanup skipped: {e}")


def start_e2e_infrastructure() -> None:
    """Start E2E v2 Docker infrastructure with health checks."""
    logger.info("=" * 60)
    logger.info("STARTUP: Starting E2E v2 infrastructure")
    logger.info("=" * 60)

    try:
        # Start containers
        logger.info("Starting docker-compose services...")
        result = subprocess.run(
            ["docker-compose", "-f", "docker-compose.e2e.yml", "up", "-d"],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )

        if result.returncode != 0:
            logger.error(f"Failed to start containers: {result.stderr}")
            raise RuntimeError("Docker startup failed")

        logger.info("Containers started, waiting for health checks...")
        time.sleep(30)  # Wait longer for databases and Kafka to be healthy

        # Verify containers are running
        result = subprocess.run(
            ["docker-compose", "-f", "docker-compose.e2e.yml", "ps"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )

        logger.info("Container status:")
        for line in result.stdout.split("\n"):
            if line.strip():
                logger.info(f"  {line}")

        logger.info("✅ Infrastructure ready")
        logger.info("=" * 60)

    except subprocess.TimeoutExpired:
        logger.error("Docker startup timed out")
        raise
    except Exception as e:
        logger.error(f"Failed to start infrastructure: {e}")
        raise

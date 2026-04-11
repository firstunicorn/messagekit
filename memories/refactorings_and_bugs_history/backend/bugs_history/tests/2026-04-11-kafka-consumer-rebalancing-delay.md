# Kafka consumer group rebalancing delay in tests

**Date:** 2026-04-11
**Status:** Documented ✅
**Severity:** High — flaky CI test failures, QueueEmpty in bridge tests

## Symptom

Tests published messages to Kafka but bridge consumer never received them. `QueueEmpty` errors in CI despite correct queue setup and exchange bindings.

## Root cause

`FastStream broker.start()` is async but returns before the Kafka consumer has fully joined the consumer group and started polling. Consumer group rebalancing takes 2-3 seconds. Tests published messages during this window before consumer was ready.

## Fix

Added 5-second `asyncio.sleep()` in `async_client_with_kafka` fixture after lifespan initialization:

```python
async with app.router.lifespan_context(app) as state:
    if state:
        app.state._state.update(state)
    # Wait for Kafka consumer group rebalancing to complete
    await asyncio.sleep(5)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
```

## Why 5 seconds

Kafka consumer group rebalancing typically takes 2-3 seconds. 5 seconds provides buffer for slow CI environments (GitHub Actions Docker-in-Docker).

## Lessons

- FastStream `broker.start()` doesn't wait for consumer readiness
- Kafka consumer group rebalancing is asynchronous and takes several seconds
- Tests must wait for consumer to be polling before publishing messages
- CI environments can be significantly slower than local development

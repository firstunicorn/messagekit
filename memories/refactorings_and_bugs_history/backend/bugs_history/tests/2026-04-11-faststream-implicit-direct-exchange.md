# FastStream implicit DIRECT exchange type

**Date:** 2026-04-11
**Status:** Documented ✅
**Severity:** High — silent message routing failures, no errors raised

## Symptom

Messages published to RabbitMQ succeeded without errors, but consuming queues received nothing. `queue.get(timeout=30)` returned None despite messages being published.

## Root cause

When `RabbitEventPublisher.__init__` receives a bare string for `default_exchange` (e.g., `"events"`), FastStream's `broker.publish()` uses an implicit DIRECT exchange type. DIRECT exchanges require exact routing key match between publish and queue binding.

Test queue was bound to exchange with `routing_key="user.created"` expecting TOPIC exchange pattern matching. Message was published to DIRECT exchange instead — routing mismatch caused silent message loss.

## Fix

Explicitly construct `RabbitExchange` with `type=ExchangeType.TOPIC` when string is passed:

```python
if isinstance(default_exchange, str):
    self._default_exchange = RabbitExchange(
        default_exchange, type=ExchangeType.TOPIC, durable=True
    )
```

## Why it's dangerous

No exception is raised. `broker.publish()` succeeds silently. Message is routed to wrong exchange type or dropped entirely. Only symptom is consumer timeout.

## Lessons

- FastStream defaults to DIRECT exchange for string exchange names
- TOPIC exchange is required for pattern-based routing (wildcards, partial matches)
- Always explicitly declare exchange type when using FastStream RabbitMQ integration

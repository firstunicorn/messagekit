# SQLAlchemy async_sessionmaker vs AsyncSession confusion

**Date:** 2026-04-11
**Status:** Documented ✅
**Severity:** Critical — idempotency completely broken

## Problem

`async_sessionmaker` (factory) passed where `AsyncSession` (instance) expected. Causes `AttributeError: 'async_sessionmaker' object has no attribute 'in_transaction'`.

## Root cause

`async_sessionmaker` is a factory that creates sessions. It is NOT a session itself. Code that expects an active `AsyncSession` will fail when given a factory.

```python
# WRONG — session_factory is a factory, not a session:
store = SqlAlchemyProcessedMessageStore(session_factory)  # AttributeError

# CORRECT — create session from factory:
async with session_factory() as session:
    store = SqlAlchemyProcessedMessageStore(session)  # Works
```

## Why it happens

Common mistake when:
1. Treating session-dependent objects as singletons (initialized once at startup)
2. Passing the factory instead of creating a session per operation
3. Not understanding that `async_sessionmaker` is callable, not a context manager

## Solution

Instantiate session-dependent objects per operation within a session context:

```python
async with session_factory() as session, session.begin():
    store = SqlAlchemyProcessedMessageStore(session)
    consumer = BridgeConsumer(store=store, ...)
    await consumer.handle_message(message)
```

## Applicable to

Any async SQLAlchemy project with session-dependent services. Common in message consumers, API handlers, and background tasks.

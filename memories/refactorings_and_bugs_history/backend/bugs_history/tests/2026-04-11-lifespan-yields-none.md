# FastAPI lifespan() yields None, not state dict

**Date:** 2026-04-11
**Status:** Documented ✅
**Severity:** Medium — TypeError in test fixtures

## Symptom

`TypeError: 'NoneType' object is not iterable` when test fixture called `app.state._state.update(state)` after `async with app.router.lifespan_context(app) as state:`.

## Root cause

FastAPI's `lifespan()` context manager yields whatever the lifespan function yields. Our lifespan function yields `None` (not a state dict), so `state` is `None` in the test fixture.

```python
# In lifespan.py:
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # ... setup ...
    yield  # yields None, not a dict

# In conftest.py:
async with app.router.lifespan_context(app) as state:
    app.state._state.update(state)  # TypeError: NoneType not iterable
```

## Fix

Guard the update call with `if state:` check:

```python
async with app.router.lifespan_context(app) as state:
    if state:
        app.state._state.update(state)
```

## Lessons

- FastAPI lifespan can yield `None` or a state dict — depends on implementation
- Test fixtures must handle both cases gracefully
- If lifespan yields `None`, brokers are still accessible via `app.state` attributes set during initialization

# Logging architecture: stdlib in prod, structlog in tests

**Date:** 2026-04-11
**Status:** Documented ✅

## Decision

Production code uses stdlib `logging` only. Tests and scripts use `structlog`.

## Rationale

Production code remains logging-library-agnostic. Any logging backend can be configured by deployers without code changes. Tests use structlog for structured output (easier debugging, JSON-formatted test logs).

## Where each is used

- `src/messaging/` — stdlib `logging` only
- `tests/conftest.py` — `structlog` for fixture output
- `scripts/cleanup_docker.py` — `structlog` for script output

## Deptry configuration

`structlog` is excluded from DEP002 checks in `pyproject.toml` since it's not imported in `src/`:

```toml
[tool.deptry.per_rule_ignores]
DEP002 = [
    "structlog",  # test/script only
]
```

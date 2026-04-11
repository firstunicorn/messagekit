# Deptry false positive: structlog flagged as unused dependency

**Date:** 2026-04-11
**Status:** Fixed ✅
**Severity:** Medium — CI Validate Dependencies job failing

## Symptom

`deptry` reported: `DEP002 'structlog' defined as a dependency but not used in the codebase`

## Root cause

`structlog` is intentionally used only in:
- `tests/conftest.py` — structured test fixture output
- `scripts/cleanup_docker.py` — Docker cleanup script logging

Production code (`src/`) uses stdlib `logging` to remain logging-library-agnostic. Deptry only scans `src/` by default, so it correctly identified that `structlog` isn't imported there.

## Fix

Added `structlog` to `DEP002` ignore list in `pyproject.toml` with architectural rationale:

```toml
[tool.deptry.per_rule_ignores]
DEP002 = [
    # structlog: used only in tests/conftest.py and scripts/cleanup_docker.py.
    # Production code remains logging-library-agnostic (stdlib logging).
    "structlog",
    ...
]
```

## Files changed

- `pyproject.toml` — added structlog to DEP002 ignores

## Lessons

- Deptry scans `src/` only — test-only and script-only dependencies trigger DEP002
- Architectural decisions (logging library agnosticism in prod) should be documented in config
- DEP002 ignores are appropriate for intentional test/script-only dependencies

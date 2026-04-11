# Vulture whitelist requires explicit file argument

**Date:** 2026-04-11
**Status:** Documented ✅
**Severity:** Medium — CI linters job failing

## Problem

Vulture doesn't auto-discover whitelist files. CI workflow must pass whitelist as positional argument.

```bash
# WRONG — ignores whitelist:
poetry run vulture src/ tests/ --exclude .venv --min-confidence 80

# CORRECT — whitelist loaded:
poetry run vulture src/ tests/ .vulture-whitelist.py --exclude .venv --min-confidence 80
```

## Common triggers

Framework-required signatures that vulture flags as unused:
- pytest hook parameters (`exitstatus` in `pytest_sessionfinish`)
- FastStream middleware factory params (`msg`, `context`)
- Fixture parameters used for side effects only

## Whitelist format

```python
# .vulture-whitelist.py
exitstatus  # Used in: pytest_sessionfinish hook
context  # Used in: circuit_breaker_factory (FastStream signature requirement)
```

## Applicable to

Any project using vulture with intentionally unused code required by framework interfaces.

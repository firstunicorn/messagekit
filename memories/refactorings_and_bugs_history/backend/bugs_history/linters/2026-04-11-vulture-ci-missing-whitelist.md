# Vulture CI missing whitelist file — false positive unused variables

**Date:** 2026-04-11
**Status:** Fixed ✅
**Severity:** Medium — CI linters job failing

## Symptom

Vulture reported unused variables in CI despite `.vulture-whitelist.py` existing:
- `context` in `circuit_breaker_factory` (FastStream middleware signature requirement)
- `exitstatus` in `pytest_sessionfinish` (pytest hook signature requirement)
- `skip_broker_in_tests` in `async_client` fixture (side-effect-only parameter)

## Root cause

GitHub Actions workflow didn't pass whitelist file to vulture command:

```yaml
# WRONG:
poetry run vulture src/ tests/ --exclude .venv --min-confidence 80

# CORRECT:
poetry run vulture src/ tests/ .vulture-whitelist.py --exclude .venv --min-confidence 80
```

Without `.vulture-whitelist.py` as argument, vulture scanned source code but ignored suppression entries.

## Fix

1. Added `.vulture-whitelist.py` to vulture command in `.github/workflows/linters.yml`
2. Updated whitelist file with correct line numbers (shifted after documentation additions)
3. Added rationale comments explaining WHY each variable is unused but required

## Files changed

- `.github/workflows/linters.yml` — added whitelist to vulture command
- `.vulture-whitelist.py` — updated line numbers, added rationale

## Lessons

- Vulture requires whitelist file as positional argument, not auto-discovery
- Line numbers in whitelist comments must be updated when code changes
- Framework-required signatures (pytest hooks, FastStream factories) will always trigger vulture

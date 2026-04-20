---
name: Rename messaging to messagekit
overview: Rename the Python import package from `messaging` to `messagekit` and the PyPI distribution from `python-eventing` to `messagekit`, achieving PEP 423 compliance (distribution = import name). GitHub URLs stay unchanged.
todos:
  - id: branch
    content: Create git branch rename/messagekit
    status: completed
  - id: directory
    content: git mv src/messaging src/messagekit
    status: completed
  - id: imports
    content: Bulk replace from messaging -> from messagekit in ~146 .py files (src/, tests/, scripts/)
    status: completed
  - id: pyproject
    content: "Update pyproject.toml: name, packages, known_first_party, coverage paths"
    status: completed
  - id: setup-cfg
    content: "Update setup.cfg: all src/messaging paths"
    status: completed
  - id: importlinter
    content: "Update .importlinter: root_package and layer references"
    status: completed
  - id: conf-py
    content: "Update docs/source/conf.py: autoapi_dirs path"
    status: completed
  - id: vulture
    content: "Update .vulture-whitelist.py: comment paths"
    status: completed
  - id: readme
    content: "Update README.md: import examples and naming explanation"
    status: completed
  - id: docs-md
    content: "Update 12 docs/*.md files: all messaging import references"
    status: completed
  - id: serena-verify
    content: "Serena MCP verification: search_for_pattern confirms zero orphaned messaging references"
    status: completed
  - id: local-tests
    content: Run pytest, ruff, mypy, lint-imports locally
    status: completed
  - id: pr
    content: Commit, push, create draft PR targeting develop, check GitHub Actions
    status: completed
isProject: false
---

# Rename `messaging` to `messagekit`

## Scope

- **Import package**: `messaging` -> `messagekit` (directory + all imports)
- **Distribution name**: `python-eventing` -> `messagekit` (pyproject.toml only)
- **GitHub URLs**: unchanged (repo rename is separate)
- **Historical files**: `.specstory/`, `memories/`, `.cursor/plans/` - NOT modified (they are history)
- **PyPI publish**: out of scope

## Impact summary

- **Directory rename**: `src/messaging/` -> `src/messagekit/` (113 files)
- **Python imports**: ~146 `.py` files across `src/`, `tests/`, `scripts/`
- **Config files**: 5 files ([pyproject.toml](pyproject.toml), [setup.cfg](setup.cfg), [.importlinter](.importlinter), [docs/source/conf.py](docs/source/conf.py), [.vulture-whitelist.py](.vulture-whitelist.py))
- **Documentation**: [README.md](README.md) + 12 docs `.md` files

## Approach

**Do NOT use sub-agents.** They are prone to errors on tasks of this scale. Execute all steps directly.

Use Serena MCP (`activate_project` first, then `search_for_pattern` for finding, `replace_content` for config/doc changes, `find_referencing_symbols` for verification). For bulk import replacement across 146+ Python files, use PowerShell `Get-ChildItem + ForEach-Object` one-liner (deterministic text replacement, not code manipulation). Serena MCP verifies no orphaned references remain.

---

## Phase 1: create branch

```powershell
cd "c:\coding\gridflow-microservices-codex-taskmaster\microservices\eventing" && git checkout -b rename/messagekit
```

## Phase 2: directory rename (preserves git history)

```powershell
git mv src/messaging src/messagekit
```

## Phase 3: bulk import replacement (Python files)

Replace `from messaging` -> `from messagekit` and `import messaging` -> `import messagekit` in all `.py` files under `src/`, `tests/`, `scripts/`. PowerShell one-liner for deterministic find-replace across ~146 files.

**Serena MCP verification after**: use `search_for_pattern` with pattern `from messaging\b` to confirm zero remaining references in `.py` files.

## Phase 4: configuration files

Each file updated individually (small, targeted changes):

### [pyproject.toml](pyproject.toml)
- Line 2: `name = "python-eventing"` -> `name = "messagekit"`
- Line 9: `packages = [{include = "messaging", from = "src"}]` -> `include = "messagekit"`
- Lines 312-324: all `src/messaging/` coverage paths -> `src/messagekit/`
- Line 357: `known_first_party = ["messaging"]` (deptry) -> `["messagekit"]`
- Line 386: `known_first_party = ["messaging"]` (isort) -> `["messagekit"]`

### [setup.cfg](setup.cfg)
- Lines 22-42: all `src/messaging/` and `src/messaging\` paths -> `src/messagekit/` and `src/messagekit\`

### [.importlinter](.importlinter)
- Line 2: `root_package = messaging` -> `root_package = messagekit`
- Lines 8-12: all `messaging.` layer references -> `messagekit.`

### [docs/source/conf.py](docs/source/conf.py)
- Line 52: `autoapi_dirs` path from `messaging` -> `messagekit`

### [.vulture-whitelist.py](.vulture-whitelist.py)
- Lines 14-15: comment paths from `src/messaging/` -> `src/messagekit/`

## Phase 5: documentation updates

### [README.md](README.md)
- Line 34: import package name explanation
- Lines 37-38, 449-450, 476-477, 523-524, 555, 562-563: all `from messaging.` code examples
- Line 50: update naming description

### docs/ markdown files (12 files)
All `from messaging.` and `import messaging` references in:
- [docs/source/integration-guide.md](docs/source/integration-guide.md)
- [docs/source/troubleshooting.md](docs/source/troubleshooting.md)
- [docs/source/dlq-handlers.md](docs/source/dlq-handlers.md)
- [docs/source/cross-service-communication.md](docs/source/cross-service-communication.md)
- [docs/source/consumer-transactions.md](docs/source/consumer-transactions.md)
- [docs/source/transactional-outbox.md](docs/source/transactional-outbox.md)
- [docs/source/kafka-rabbitmq-features.md](docs/source/kafka-rabbitmq-features.md)
- [docs/source/index.md](docs/source/index.md)
- [docs/eventbus/usage-guide.md](docs/eventbus/usage-guide.md)
- [docs/deployment/quickstart-docker-kafka.md](docs/deployment/quickstart-docker-kafka.md)
- [docs/confluent-backend-migration.md](docs/confluent-backend-migration.md)
- [docs/testing/strategy/coverage-strategy.md](docs/testing/strategy/coverage-strategy.md)

## Phase 6: Serena MCP final verification

1. `search_for_pattern` with `from messaging[.\s]` restricted to `*.py` - must return 0 results
2. `search_for_pattern` with `"messaging"` restricted to `pyproject.toml`, `setup.cfg`, `.importlinter` - must return 0 results
3. `find_referencing_symbols` on key symbols (`BaseEvent`, `EventBus`, `SqlAlchemyOutboxRepository`) to confirm import paths resolve

## Phase 7: local test run

```powershell
cd "c:\coding\gridflow-microservices-codex-taskmaster\microservices\eventing" && .venv\Scripts\activate.bat && poetry install --with test --no-interaction && poetry run pytest tests/ -v -m "not manual" --timeout=300
```

Run linters:
```powershell
poetry run ruff check src/ tests/ && poetry run mypy src/ && poetry run lint-imports
```

## Phase 8: commit and create PR

- Single commit: `refactor(rename): rename import package from messaging to messagekit`
- Push branch, create draft PR targeting `develop` (triggers CI: tests, linters, validate-deps)
- Monitor GitHub Actions results

## Files NOT modified (intentional)

- `.specstory/` - dialogue history (frozen records)
- `memories/` - AI lessons (reference old names, that's fine)
- `.cursor/plans/` - historical plans
- `.cursor/rules/` - one reference in `git-commits.mdc` but it's an example, not functional code
- GitHub workflow YML files - no direct `messaging` references

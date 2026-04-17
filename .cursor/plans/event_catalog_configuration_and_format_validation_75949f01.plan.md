---
name: Event catalog configuration and format validation
overview: Complete event catalog system in 3 commits - EventCatalogSettings + format validators (Commit 1), EventCatalogManager + Git integration (Commit 2), BaseEvent catalog validation integration (Commit 3). Catalog uses TOML for registries and JSON for detailed schemas.
todos: []
isProject: false
---

# Event catalog configuration and format validation (multi-commit)

## Repository naming

**Recommended name:** `event-catalog`

**Rationale:**
- Clear purpose (catalog of events)
- Generic (not tied to Kafka/tech)
- Industry-standard term
- Short, memorable
- Similar to Confluent's "Schema Registry"

**Alternative options considered:**
- `domain-events-registry` (90/100) - Emphasizes DDD, but longer
- `messaging-contracts` (85/100) - Matches library name, but too generic
- `event-schemas` (80/100) - Simple, but doesn't convey service registry aspect

## Implementation approach

**Serena MCP usage:**
- **CRITICAL**: Serena MCP MUST be used for all modifications to existing files
- Use standard file tools for creating new files
- Activate project with Serena MCP before starting: Call `activate_project` tool
- Use `get_symbols_overview` and `find_symbol` for exploration
- Use `replace_symbol_body` and `insert_after_symbol` for code modifications
- Use `find_referencing_symbols` to verify no breaking changes

Three-commit strategy for complete event catalog system:

**Commit 1:** EventCatalogSettings + format validators
- Configuration infrastructure
- Format validation (no catalog lookup yet)
- Tests for validators and settings

**Commit 2:** EventCatalogManager + Git integration
- Git clone/pull/cache logic
- TOML/JSON parsing
- Catalog data loading
- Tests for manager

**Commit 3:** BaseEvent catalog validation integration
- Layer 2 validation (catalog lookup)
- Integration with BaseEvent validators
- End-to-end tests

---

## COMMIT 1: EventCatalogSettings + format validators

**Serena MCP Note:** This commit modifies existing files (base_event.py, base_settings.py). Must activate Serena MCP project before starting and use Serena's symbol manipulation tools for all code changes to existing files.

### Files to create

### 1. Event catalog settings
**File:** `src/messaging/config/event_catalog_settings.py`

Configuration class for external event catalog repositories:
- `repo_url`: Git URL (e.g., https://github.com/org/event-catalog.git)
- `branch`: Branch to fetch (default: "main")
- `local_path`: Local cache directory (default: "./.event-catalog")
- `refresh_interval`: Auto-refresh interval in seconds (default: 3600)
- `strict_mode`: Reject vs warn for catalog mismatches (default: False)

All configurable via `EVENT_CATALOG_*` environment variables.

### 2. Validation tests
**File:** `tests/unit/core/test_event_validation.py`

Test event_type and source validators:
- Valid formats pass (orders.order.created, payment-api)
- Invalid formats rejected with clear messages
- Edge cases: uppercase, spaces, underscores, special chars
- Error messages guide developers to correct format

### 3. Configuration tests
**Files:**
- `tests/unit/config/__init__.py` (new folder)
- `tests/unit/config/test_event_catalog_settings.py`

Test EventCatalogSettings:
- Loads from environment variables correctly
- Default values work
- Optional configuration (no repo_url) handled
- All fields validated properly

## Files to modify

### 4. BaseEvent validators
**File:** [src/messaging/core/contracts/base_event.py](src/messaging/core/contracts/base_event.py)

**CRITICAL: Use Serena MCP for existing code modifications**
- Use `get_symbols_overview` to see BaseEvent class structure
- Use `find_symbol` with `name_path="BaseEvent"` and `depth=1` to see all methods
- Use `insert_after_symbol` to add validators after the last field definition
- Verify with `find_referencing_symbols` before making changes

Add field validators (lines 30-38 area):

```python
@field_validator("event_type")
@classmethod
def validate_event_type_format(cls, value: str) -> str:
    """Enforce domain.entity.event naming convention.

    Examples: orders.order.created, payments.transaction.completed
    Pattern: lowercase letters, dots between segments, hyphens within segments.
    """
    pattern = r"^[a-z]+\.[a-z-]+\.[a-z-]+$"
    if not re.match(pattern, value):
        raise ValueError(
            f"event_type must match pattern: domain.entity.event\n"
            f"Expected: lowercase with dots (e.g., orders.order.created)\n"
            f"Got: {value}"
        )
    return value

@field_validator("source")
@classmethod
def validate_source_format(cls, value: str) -> str:
    """Enforce lowercase-with-hyphens service naming convention.

    Examples: order-service, payment-api, user-service
    Pattern: starts with letter, lowercase alphanumeric and hyphens only.
    """
    pattern = r"^[a-z][a-z0-9-]*$"
    if not re.match(pattern, value):
        raise ValueError(
            f"source must be lowercase-with-hyphens\n"
            f"Expected: lowercase, hyphens, numbers (e.g., order-service)\n"
            f"Got: {value}"
        )
    return value
```

Import `re` at top of file.

### 5. Settings integration
**File:** [src/messaging/config/base_settings.py](src/messaging/config/base_settings.py)

**CRITICAL: Use Serena MCP for existing code modifications**
- Use `get_symbols_overview` to see Settings class structure
- Use `find_symbol` with `name_path="Settings"` to see class definition
- Use Serena's symbol manipulation to add EventCatalogSettings to inheritance list
- Verify no circular imports with `find_referencing_symbols`

Extend Settings to include EventCatalogSettings (line 21-26 area):

```python
from messaging.config.event_catalog_settings import EventCatalogSettings

class Settings(
    BaseFastAPISettings,
    BaseDatabaseSettings,
    KafkaSettings,
    RabbitMQSettings,
    EventCatalogSettings,  # Add this
):
```

All EVENT_CATALOG_* environment variables now available.

### 6. Config exports
**File:** [src/messaging/config/__init__.py](src/messaging/config/__init__.py)

Add EventCatalogSettings to exports (line 3-5 area):

```python
from messaging.config.base_settings import Settings, settings
from messaging.config.event_catalog_settings import EventCatalogSettings

__all__ = ["Settings", "settings", "EventCatalogSettings"]
```

## Validation impact

**Existing tests:** All existing test events already conform to patterns (verified via grep):
- `gamification.XPAwarded` ✓
- `user.created` ✓
- `order.completed` ✓
- `gamification-service` ✓
- `e2e-test-v2` ✓

**Breaking change:** Any future events with non-conforming names will fail at instantiation.

## Configuration example

```bash
# .env (optional - Phase 1 works without catalog)
EVENT_CATALOG_REPO_URL=https://github.com/your-org/event-catalog.git
EVENT_CATALOG_BRANCH=main
EVENT_CATALOG_STRICT_MODE=false
EVENT_CATALOG_REFRESH_INTERVAL=3600
```

## Commit 1 details

**Type:** `feat(events)` - new feature
**Scope:** events/configuration
**Breaking:** Yes (enforces naming conventions)

**Message:**
```
feat(events): add event catalog config and format validation

Commit 1/3: EventCatalogSettings + format validators (no catalog integration yet).

## Starting point
Events had minimal validation (min_length only). No standardization for:
- event_type naming convention (domain.entity.event)
- source naming convention (lowercase-with-hyphens)
- Configuration for external event catalogs

## Changes

### Configuration (src/messaging/config/event_catalog_settings.py)
- New EventCatalogSettings with:
  - repo_url: Git URL for external event catalog
  - branch: Branch to fetch from catalog
  - local_path: Local cache directory
  - refresh_interval: Auto-refresh interval (seconds)
  - strict_mode: Reject vs warn for catalog mismatches
- All configurable via EVENT_CATALOG_* env vars
- Optional (falls back to format-only validation if not configured)

### Validation (src/messaging/core/contracts/base_event.py)
- event_type validator: Enforces domain.entity.event pattern
  - Pattern: ^[a-z]+\.[a-z-]+\.[a-z-]+$
  - Examples: orders.order.created, payments.transaction.completed
- source validator: Enforces lowercase-with-hyphens
  - Pattern: ^[a-z][a-z0-9-]*$
  - Examples: order-service, payment-api, user-service
- Validators run on event instantiation (fail fast)

### Integration (src/messaging/config/base_settings.py)
- Settings now extends EventCatalogSettings
- Inherits all EVENT_CATALOG_* configuration options
- Backward compatible (all catalog settings optional)

### Tests
- tests/unit/core/test_event_validation.py:
  - Valid formats pass
  - Invalid formats rejected with clear error messages
  - Edge cases (uppercase, spaces, special chars)
- tests/unit/config/test_event_catalog_settings.py:
  - Settings load from environment variables
  - Default values work correctly
  - Optional configuration handled

## Result
Events now enforce naming conventions at creation time. Organizations can configure
external event catalogs via environment variables (catalog manager in Commit 2).

BREAKING CHANGE: Existing events with non-conforming names will fail validation.
```

---

## COMMIT 2: EventCatalogManager + Git integration

### Files to create

#### 1. Catalog manager
**File:** `src/messaging/catalog/__init__.py`
```python
"""Event catalog management."""
from messaging.catalog.manager import EventCatalogManager

__all__ = ["EventCatalogManager"]
```

**File:** `src/messaging/catalog/manager.py`

EventCatalogManager class that:
- Manages local cache of external event catalog repository
- Git clone/pull operations with subprocess
- TOML parsing for events.toml and services.toml
- Caches catalog data in memory
- Auto-refresh based on refresh_interval
- Validates event types and service names against catalog

Key methods:
```python
class EventCatalogManager:
    def __init__(self, settings: EventCatalogSettings)
    async def ensure_catalog(self) -> dict | None
    def _needs_refresh(self) -> bool
    async def _refresh_catalog(self) -> None  # Git clone or pull
    def _load_catalog(self) -> None  # Parse TOML files
    def _load_toml(self, path: Path) -> dict  # TOML parser
    def validate_event_type(self, event_type: str) -> tuple[bool, str]
    def validate_service_name(self, service_name: str) -> tuple[bool, str]
```

**Implementation notes:**
- Use `tomllib` (Python 3.11+) or `tomli` (Python 3.10) for TOML parsing
- Git operations via `subprocess.run()` (not async)
- Return `None` if no catalog configured (repo_url is None)
- Cache last refresh timestamp to avoid excessive Git pulls
- Support both strict mode (reject) and warn mode (log warning)

#### 2. Catalog manager tests
**Files:**
- `tests/unit/catalog/__init__.py` (new folder)
- `tests/unit/catalog/test_catalog_manager.py`

Test EventCatalogManager:
- Initialization with settings
- Git clone on first call (mock subprocess)
- Git pull on subsequent calls (mock subprocess)
- TOML parsing (events.toml, services.toml)
- Catalog data caching
- Refresh interval logic
- Event type validation (found, not found, strict/warn modes)
- Service name validation (found, not found, strict/warn modes)
- No catalog configured (returns None)

#### 3. Integration test fixtures
**File:** `tests/integration/catalog/__init__.py` (new folder)
**File:** `tests/integration/catalog/fixtures/events.toml`
```toml
[events."orders.order.created"]
owner_service = "order-service"
owner_team = "commerce"
added_date = "2026-01-15"
schema_version = "1.0"
description = "Test event"
```

**File:** `tests/integration/catalog/fixtures/services.toml`
```toml
[services.order-service]
team = "commerce"
contact = "team@example.com"
repository = "https://github.com/org/order-service"
events_published = ["orders.order.created"]
events_consumed = []
```

### Files to modify

#### 4. Update dependencies
**File:** [pyproject.toml](pyproject.toml)

Add TOML parser to dependencies (line 11-29 area):
```toml
[tool.poetry.dependencies]
python = "^3.12"
# ... existing dependencies ...
tomli = "^2.0.1"  # TOML parser for Python <3.11 (backport of tomllib)
```

Note: Python 3.12 has `tomllib` built-in, but add `tomli` for backward compatibility if needed.

### Commit 2 details

**Type:** `feat(catalog)` - new feature
**Scope:** catalog/manager

**Message:**
```
feat(catalog): add event catalog manager with Git integration

Commit 2/3: EventCatalogManager handles Git clone/pull and TOML parsing.

## Starting point
EventCatalogSettings existed but no implementation to fetch/parse catalogs.
Format validators worked but couldn't check against actual catalog registry.

## Changes

### Catalog Manager (src/messaging/catalog/manager.py)
- EventCatalogManager class:
  - Git clone on first access (--depth 1 for performance)
  - Git pull on refresh (based on refresh_interval setting)
  - TOML parsing for events.toml and services.toml
  - In-memory caching of catalog data
  - Event type validation against catalog
  - Service name validation against catalog
  - Strict mode (reject) vs warn mode (log only)
- Uses subprocess for Git operations (shell=False for security)
- Uses tomllib/tomli for TOML parsing

### Dependencies (pyproject.toml)
- Added tomli for TOML parsing (Python 3.11+ has tomllib built-in)

### Tests
- tests/unit/catalog/test_catalog_manager.py:
  - Git operations (mocked subprocess)
  - TOML parsing
  - Catalog validation logic
  - Refresh interval behavior
  - Strict vs warn mode
- tests/integration/catalog/:
  - Fixture catalog files (events.toml, services.toml)
  - Integration tests with real TOML files

## Result
Organizations can now point library to external Git catalogs. Manager automatically
clones, caches, and validates events/services against catalog registries.
Integration with BaseEvent validators in Commit 3.
```

---

## COMMIT 3: BaseEvent catalog validation integration

**Serena MCP Note:** This commit modifies existing file (base_event.py) to add Layer 2 validation. Must use Serena MCP's `replace_symbol_body` to update the existing validators created in Commit 1.

### Files to modify

#### 1. BaseEvent catalog integration
**File:** [src/messaging/core/contracts/base_event.py](src/messaging/core/contracts/base_event.py)

**CRITICAL: Use Serena MCP for existing code modifications**
- Use `get_symbols_overview` to see current BaseEvent structure
- Use `find_symbol` with `name_path="BaseEvent/validate_event_type_format"` to locate existing validator
- Use `find_symbol` with `name_path="BaseEvent/validate_source_format"` to locate existing validator
- Use `replace_symbol_body` to update validator methods with Layer 2 validation
- Add imports using `insert_after_symbol` at module level
- Verify with `find_referencing_symbols` before making changes

Add global catalog manager and Layer 2 validation (after imports, before BaseEvent class):

```python
import asyncio
import re
from messaging.config.event_catalog_settings import EventCatalogSettings
from messaging.catalog.manager import EventCatalogManager

# Global catalog manager (initialized once at module load)
_catalog_settings = EventCatalogSettings()
_catalog_manager = (
    EventCatalogManager(_catalog_settings) 
    if _catalog_settings.repo_url else None
)
```

Update validators to add Layer 2 (catalog validation):

```python
@field_validator("event_type")
@classmethod
def validate_event_type_format(cls, value: str) -> str:
    """Validate event type format and against catalog."""
    # Layer 1: Format validation (existing)
    pattern = r"^[a-z]+\.[a-z-]+\.[a-z-]+$"
    if not re.match(pattern, value):
        raise ValueError(
            f"event_type must match pattern: domain.entity.event\n"
            f"Expected: lowercase with dots (e.g., orders.order.created)\n"
            f"Got: {value}"
        )
    
    # Layer 2: Catalog validation (new)
    if _catalog_manager:
        catalog = asyncio.run(_catalog_manager.ensure_catalog())
        if catalog:
            is_valid, message = _catalog_manager.validate_event_type(value)
            if not is_valid:
                raise ValueError(message)
            elif "Warning" in message:
                logger.warning(message)
    
    return value

@field_validator("source")
@classmethod
def validate_source_format(cls, value: str) -> str:
    """Validate source format and against catalog."""
    # Layer 1: Format validation (existing)
    pattern = r"^[a-z][a-z0-9-]*$"
    if not re.match(pattern, value):
        raise ValueError(
            f"source must be lowercase-with-hyphens\n"
            f"Expected: lowercase, hyphens, numbers (e.g., order-service)\n"
            f"Got: {value}"
        )
    
    # Layer 2: Catalog validation (new)
    if _catalog_manager:
        catalog = asyncio.run(_catalog_manager.ensure_catalog())
        if catalog:
            is_valid, message = _catalog_manager.validate_service_name(value)
            if not is_valid:
                raise ValueError(message)
            elif "Warning" in message:
                logger.warning(message)
    
    return value
```

Add logger import at top of file if not present:
```python
import logging
logger = logging.getLogger(__name__)
```

### Files to create

#### 2. End-to-end catalog validation tests
**File:** `tests/integration/catalog/test_catalog_validation_e2e.py`

End-to-end tests:
- Event with valid event_type in catalog (passes)
- Event with valid source in catalog (passes)
- Event with invalid event_type (strict mode rejects)
- Event with invalid event_type (warn mode allows, logs warning)
- Event with invalid source (strict mode rejects)
- Event with invalid source (warn mode allows, logs warning)
- No catalog configured (format validation only)
- Git catalog auto-refresh after interval
- Multiple organizations using different catalog repos

Use tmpdir fixtures to create temporary Git repositories with test catalogs.

### Commit 3 details

**Type:** `feat(events)` - new feature
**Scope:** events/validation

**Message:**
```
feat(events): integrate catalog validation with BaseEvent

Commit 3/3: BaseEvent now validates against external catalogs (Layer 2).

## Starting point
Format validators worked (Layer 1) but didn't check actual catalog registries.
EventCatalogManager existed but wasn't integrated into BaseEvent validation.

## Changes

### BaseEvent Integration (src/messaging/core/contracts/base_event.py)
- Global catalog manager initialized at module load
- Layer 2 validation added to event_type and source validators:
  - After format validation passes
  - Calls catalog manager to validate against registry
  - Strict mode: Rejects events not in catalog
  - Warn mode: Logs warning but allows events not in catalog
  - No catalog: Skips Layer 2 (format-only validation)
- Uses asyncio.run() for catalog manager (async methods)
- Logs warnings for unregistered events in warn mode

### Tests (tests/integration/catalog/test_catalog_validation_e2e.py)
- End-to-end validation flows:
  - Valid events in catalog (pass)
  - Invalid events in catalog (strict mode rejects)
  - Invalid events in catalog (warn mode logs warning)
  - No catalog configured (format-only)
  - Auto-refresh behavior
  - Multiple organization catalogs
- Uses tmpdir fixtures for temporary Git repos

## Result
Complete catalog validation system. Organizations can:
- Point library to external Git catalog via ENV vars
- Enforce event type/service name registration (strict mode)
- Or warn about unregistered events (warn mode)
- Or skip catalog entirely (development mode)

Library automatically clones, caches, and refreshes catalogs. Validation happens
at event instantiation (fail fast).
```

---

## Usage in different organizations

### Organization A (strict production)
```bash
# .env
EVENT_CATALOG_REPO_URL=https://github.com/your-org/event-catalog.git
EVENT_CATALOG_BRANCH=main
EVENT_CATALOG_STRICT_MODE=true
EVENT_CATALOG_REFRESH_INTERVAL=3600  # 1 hour
EVENT_CATALOG_LOCAL_PATH=/var/cache/event-catalog
```

### Organization B (warn staging)
```bash
# .env
EVENT_CATALOG_REPO_URL=https://github.com/another-company/messaging-events.git
EVENT_CATALOG_BRANCH=production
EVENT_CATALOG_STRICT_MODE=false  # Warn only, don't block
EVENT_CATALOG_REFRESH_INTERVAL=1800  # 30 minutes
EVENT_CATALOG_LOCAL_PATH=/var/cache/event-catalog
```

### Organization C (no catalog - development)
```bash
# .env
# EVENT_CATALOG_REPO_URL not set
# Uses format validation only (Layer 1)
```

---

## Developer workflow for adding events to catalog

Once the catalog repository is set up, teams follow this workflow:

1. **Fork `event-catalog` repository**
   ```bash
   gh repo fork your-org/event-catalog --clone
   ```

2. **Create feature branch**
   ```bash
   git checkout -b add-order-cancelled
   ```

3. **Add event to `events.toml`**
   ```toml
   [events."orders.order.cancelled"]
   owner_service = "order-service"
   owner_team = "commerce"
   added_date = "2026-04-15"
   schema_version = "1.0"
   description = "Emitted when order is cancelled by customer or admin"
   schema_file = "schemas/orders/order-cancelled.schema.json"
   ```

4. **(Optional) Create detailed JSON Schema**
   ```bash
   # Create schemas/orders/order-cancelled.schema.json
   # Full JSON Schema with properties, validation rules, examples
   ```

5. **Update service registry in `services.toml`**
   ```toml
   [services.order-service]
   # ... existing fields ...
   events_published = [
     "orders.order.created",
     "orders.order.shipped",
     "orders.order.cancelled"  # Add new event
   ]
   ```

6. **Create Pull Request**
   - CI validates TOML syntax
   - CI checks event naming conventions
   - CI validates no duplicates
   - Team reviews and approves
   - Merge to main

7. **Library auto-refreshes**
   - Services using the library will pull updates within refresh_interval (default 1 hour)
   - Or restart services for immediate refresh
   - New events now validated against catalog

## Benefits summary

**For organizations:**
- Each organization controls their own catalog (Git repository)
- Library is catalog-agnostic (point to any repo)
- Works offline (local cache)
- Zero runtime dependencies (no registry service)
- PR-based governance (team review, CI validation)

**For developers:**
- Enforced naming conventions (no typos, consistent patterns)
- Discovery via catalog browsing (see all events/services)
- Optional detailed schemas (JSON Schema for validation)
- Fast validation (in-memory cache, Git pull only on refresh)
- Clear error messages (format + catalog mismatches)

**For teams:**
- Visibility into event ownership (who owns what)
- Cross-team coordination (see events published/consumed)
- Schema evolution tracking (Git history)
- CI-validated consistency (no manual checks)

---

## Event catalog repository structure

**Format:** TOML for registries, JSON for detailed schemas

```
event-catalog/
├── README.md
├── events.toml                    # All events metadata (simple registry)
├── services.toml                  # All services metadata
└── schemas/                       # Optional: detailed JSON Schemas
    ├── orders/
    │   ├── order-created.schema.json
    │   └── order-shipped.schema.json
    └── payments/
        └── payment-completed.schema.json
```

**Example `events.toml`:**
```toml
[events."orders.order.created"]
owner_service = "order-service"
owner_team = "commerce"
added_date = "2026-01-15"
schema_version = "1.0"
description = "Emitted when a new order is placed"
schema_file = "schemas/orders/order-created.schema.json"  # Optional reference
```

**Example `services.toml`:**
```toml
[services.order-service]
team = "commerce"
contact = "commerce-team@company.com"
repository = "https://github.com/your-org/order-service"
events_published = ["orders.order.created", "orders.order.shipped"]
events_consumed = ["payments.transaction.completed"]
```

**Example `schemas/orders/order-created.schema.json`:**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["event_id", "event_type", "order_id"],
  "properties": {
    "event_id": {"type": "string", "format": "uuid"},
    "event_type": {"type": "string", "const": "orders.order.created"},
    "order_id": {"type": "string"},
    "items": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "product_id": {"type": "string"},
          "quantity": {"type": "integer", "minimum": 1}
        }
      }
    }
  }
}
```

**Why TOML + JSON:**
- TOML perfect for flat config (registries with simple metadata)
- JSON native format for JSON Schemas (full tooling support)
- No format conversion needed
- Industry standard for both use cases

## Summary

**Complete implementation across 3 commits:**

1. **Commit 1:** EventCatalogSettings + format validators
   - Configuration infrastructure (ENV vars)
   - Format validation (Layer 1)
   - Tests for validators and settings
   - Breaking change: Enforces naming conventions

2. **Commit 2:** EventCatalogManager + Git integration
   - Git clone/pull/cache logic
   - TOML parsing (events.toml, services.toml)
   - Catalog validation methods
   - Tests for manager

3. **Commit 3:** BaseEvent catalog validation integration
   - Layer 2 validation (catalog lookup)
   - Integration with BaseEvent validators
   - End-to-end tests
   - Complete catalog validation system

**Repository:** `event-catalog` (TOML + JSON)
- `events.toml`: Simple event registry
- `services.toml`: Service registry
- `schemas/*.schema.json`: Optional detailed JSON Schemas

**Configuration:** Via environment variables
- `EVENT_CATALOG_REPO_URL`: Git URL (optional)
- `EVENT_CATALOG_BRANCH`: Branch name (default: main)
- `EVENT_CATALOG_STRICT_MODE`: Reject vs warn (default: false)
- `EVENT_CATALOG_REFRESH_INTERVAL`: Refresh interval in seconds (default: 3600)
- `EVENT_CATALOG_LOCAL_PATH`: Local cache directory (default: ./.event-catalog)
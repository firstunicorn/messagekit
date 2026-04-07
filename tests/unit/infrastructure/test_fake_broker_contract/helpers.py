"""Contract tests for test fakes against real library interfaces.

Validates that test doubles (fakes, mocks) maintain signature compatibility
with their real counterparts from external libraries.

WHY THIS TEST EXISTS
====================
FakeKafkaBroker is intentionally implemented from DOCUMENTATION, not by copying
the real FastStream KafkaBroker class. This contract test validates that:

1. Official documentation matches actual implementation
2. Our documentation-based fake stays in sync with library updates
3. We catch breaking changes before integration tests fail

This approach avoids circular validation:
- BAD: Copy real class → test checks copy matches real (circular, no value)
- GOOD: Implement from docs → test checks docs match real (catches drift)

NO KAFKA INSTANCE NEEDED
=========================
This test uses inspect.signature() to compare Python class definitions at
import time. It does NOT require:
- Running Kafka broker
- Testcontainers
- Network connections
- Docker

It only needs the FastStream library installed to inspect the KafkaBroker class.

WHAT IT CATCHES
===============
Real bugs caught during implementation:
- Missing parameter: no_confirm (not in docs we initially checked)
- Wrong defaults: correlation_id was "" instead of None
- Type mismatches: runtime types vs. string annotations

If FastStream changes their API (new param, different default, etc.), this test
will fail immediately during pytest, long before integration tests run.
"""

from __future__ import annotations

import inspect
import types


def normalize_annotation(annotation: object) -> str:
    """Normalize annotations for comparison (handle runtime vs string annotations).

    Python can represent type annotations differently at runtime:
    - Sometimes as type objects (e.g., <class 'str'>)
    - Sometimes as string literals (e.g., "str")
    - Sometimes as Union types (e.g., types.UnionType)

    This normalizer converts all variants to comparable strings.
    """
    if annotation == inspect.Parameter.empty:
        return "empty"
    if isinstance(annotation, type):
        return annotation.__name__
    if isinstance(annotation, types.UnionType):
        return str(annotation).replace("typing.", "")
    return str(annotation).replace("typing.", "")

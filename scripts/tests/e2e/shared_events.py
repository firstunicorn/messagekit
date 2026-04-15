"""Shared event models for E2E tests."""

import sys
from pathlib import Path
from typing import Any

# Add src to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from messaging.core.contracts import BaseEvent


class TestEvent(BaseEvent):
    """Test event for E2E validation."""
    
    event_type: str = "test.event_emitted"
    aggregate_id: str
    user_id: int
    action: str
    metadata: dict[str, Any]

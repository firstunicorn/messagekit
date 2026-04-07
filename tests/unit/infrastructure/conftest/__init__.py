"""Shared test fixtures for infrastructure tests."""

from tests.unit.infrastructure.conftest.fixtures_base import (
    ExampleEvent,
    FakeBroker,
    FakePublisher,
    FakeRepository,
)
from tests.unit.infrastructure.conftest.fixtures_kafka import FakeKafkaBroker

__all__ = [
    "ExampleEvent",
    "FakeBroker",
    "FakeKafkaBroker",
    "FakePublisher",
    "FakeRepository",
]

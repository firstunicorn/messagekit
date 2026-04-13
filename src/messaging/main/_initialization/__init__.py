"""Initialization helpers - re-exports."""

from messaging.main._initialization.app_state import attach_state_to_app
from messaging.main._initialization.bridge_setup import (
    initialize_bridge_config,
    register_bridge_handler,
)
from messaging.main._initialization.broker_setup import initialize_brokers_and_publishers

__all__ = [
    "attach_state_to_app",
    "initialize_bridge_config",
    "initialize_brokers_and_publishers",
    "register_bridge_handler",
]

"""Test FastStream middleware execution order."""

import asyncio
import json
from typing import Any

import pytest
from confluent_kafka import Producer
from faststream.confluent import KafkaBroker

from .middleware_helpers import LifecycleTrackingMiddleware


@pytest.mark.integration
@pytest.mark.requires_kafka
class TestMiddlewareLifecycle:
    """Test FastStream middleware execution order."""

    @pytest.mark.asyncio
    async def test_middleware_execution_order(self, kafka_container) -> None:
        """Verify middleware lifecycle: on_receive → consume_scope → handler."""
        tracker = LifecycleTrackingMiddleware()

        def middleware_factory(msg=None, **kwargs) -> LifecycleTrackingMiddleware:
            return tracker

        broker = KafkaBroker(
            bootstrap_servers=kafka_container.get_bootstrap_server(),
            middlewares=[middleware_factory],
            graceful_timeout=1.0,
        )

        @broker.subscriber("test-lifecycle", group_id="lifecycle-group")
        async def handler(message: dict[str, Any]) -> None:
            tracker.call_log.append("handler")

        async with broker:
            await broker.start()
            await asyncio.sleep(5)

            producer = Producer({
                "bootstrap.servers": kafka_container.get_bootstrap_server()
            })
            test_msg = {"event_id": "lifecycle-test"}
            producer.produce("test-lifecycle", value=json.dumps(test_msg).encode())
            producer.flush()

            await asyncio.sleep(8)

            assert "on_receive" in tracker.call_log
            assert "consume_scope_start" in tracker.call_log
            assert "handler" in tracker.call_log
            assert "consume_scope_end" in tracker.call_log
            assert "after_processed(exc=False)" in tracker.call_log

            on_receive_idx = tracker.call_log.index("on_receive")
            consume_start_idx = tracker.call_log.index("consume_scope_start")
            handler_idx = tracker.call_log.index("handler")
            consume_end_idx = tracker.call_log.index("consume_scope_end")

            assert on_receive_idx < consume_start_idx
            assert consume_start_idx < handler_idx
            assert handler_idx < consume_end_idx

    @pytest.mark.asyncio
    async def test_middleware_chain_with_exception(self, kafka_container) -> None:
        """Verify after_processed is called even when handler raises exception."""
        tracker = LifecycleTrackingMiddleware()

        def middleware_factory(msg=None, **kwargs) -> LifecycleTrackingMiddleware:
            return tracker

        broker = KafkaBroker(
            bootstrap_servers=kafka_container.get_bootstrap_server(),
            middlewares=[middleware_factory],
            graceful_timeout=1.0,
        )

        @broker.subscriber("test-exc-lifecycle", group_id="exc-lifecycle-group")
        async def handler(message: dict[str, Any]) -> None:
            tracker.call_log.append("handler")
            raise RuntimeError("Test exception")

        async with broker:
            await broker.start()
            await asyncio.sleep(5)

            producer = Producer({
                "bootstrap.servers": kafka_container.get_bootstrap_server()
            })
            test_msg = {"event_id": "exc-test"}
            producer.produce("test-exc-lifecycle", value=json.dumps(test_msg).encode())
            producer.flush()

            await asyncio.sleep(8)

            assert "after_processed(exc=True)" in tracker.call_log

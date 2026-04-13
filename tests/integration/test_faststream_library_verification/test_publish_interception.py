"""Test publish_scope intercepts all publish methods."""

import asyncio
from typing import Any

import pytest
from faststream import BaseMiddleware, PublishCommand
from faststream.confluent import KafkaBroker


@pytest.mark.integration
@pytest.mark.requires_kafka
class TestPublishScopeInterception:
    """Test publish_scope intercepts all publish methods."""

    @pytest.mark.asyncio
    async def test_publish_scope_intercepts_broker_publish(
        self, kafka_container
    ) -> None:
        """Verify publish_scope intercepts direct broker.publish() calls."""

        class PublishTrackingMiddleware(BaseMiddleware):
            def __init__(self, msg: Any = None) -> None:
                """Initialize middleware with msg parameter."""
                self.msg = msg
                self.publish_calls: list[dict[str, Any]] = []

            async def publish_scope(
                self, call_next: Any, cmd: PublishCommand
            ) -> Any:
                self.publish_calls.append({"body": cmd.body})
                return await call_next(cmd)

        tracker = PublishTrackingMiddleware()

        def middleware_factory(msg=None, **kwargs) -> PublishTrackingMiddleware:
            return tracker

        broker = KafkaBroker(
            bootstrap_servers=kafka_container.get_bootstrap_server(),
            middlewares=[middleware_factory],
            graceful_timeout=1.0,
        )

        async with broker:
            await broker.start()
            await asyncio.sleep(3)

            await broker.publish({"test": "data"}, topic="test-publish-intercept")

            await asyncio.sleep(3)

            assert len(tracker.publish_calls) > 0
            assert tracker.publish_calls[0]["body"] == {"test": "data"}

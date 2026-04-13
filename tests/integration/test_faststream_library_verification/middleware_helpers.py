"""Helper middleware for lifecycle tracking tests."""

from typing import Any

from faststream import BaseMiddleware, PublishCommand, StreamMessage


class LifecycleTrackingMiddleware(BaseMiddleware):
    """Middleware that logs execution order for lifecycle verification."""

    def __init__(self, msg: Any = None) -> None:
        """Initialize middleware with msg parameter."""
        self.msg = msg
        self.call_log: list[str] = []

    async def on_receive(self) -> Any:
        self.call_log.append("on_receive")
        return await super().on_receive()

    async def consume_scope(
        self, call_next: Any, msg: StreamMessage[Any]
    ) -> Any:
        self.call_log.append("consume_scope_start")
        result = await call_next(msg)
        self.call_log.append("consume_scope_end")
        return result

    async def publish_scope(
        self, call_next: Any, cmd: PublishCommand
    ) -> Any:
        self.call_log.append("publish_scope_start")
        result = await call_next(cmd)
        self.call_log.append("publish_scope_end")
        return result

    async def after_processed(
        self,
        exc_type: type[BaseException] | None = None,
        exc_val: BaseException | None = None,
        exc_tb: Any = None,
    ) -> bool | None:
        self.call_log.append(f"after_processed(exc={exc_type is not None})")
        return await super().after_processed(exc_type, exc_val, exc_tb)

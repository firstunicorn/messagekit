"""Unit tests for RabbitMQ event publisher."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from messaging.infrastructure.pubsub.rabbit.publisher import RabbitEventPublisher


class TestRabbitEventPublisher:
    """Test RabbitMQ event publisher."""

    @pytest.mark.asyncio
    async def test_publish_to_exchange_with_explicit_routing_key(self) -> None:
        """Publisher sends event to specified exchange with routing key."""
        mock_broker = MagicMock()
        mock_broker.publish = AsyncMock()

        publisher = RabbitEventPublisher(
            broker=mock_broker,
            default_exchange="events",
        )

        event = {"event_id": "123", "event_type": "user.created"}
        await publisher.publish_to_exchange(
            event,
            routing_key="user.created",
            exchange="custom-exchange",
        )

        mock_broker.publish.assert_called_once_with(
            message=event,
            exchange="custom-exchange",
            routing_key="user.created",
        )

    @pytest.mark.asyncio
    async def test_publish_uses_default_exchange(self) -> None:
        """Publisher uses default exchange when not specified."""
        mock_broker = MagicMock()
        mock_broker.publish = AsyncMock()

        publisher = RabbitEventPublisher(
            broker=mock_broker,
            default_exchange="default-events",
        )

        event = {"event_id": "456", "event_type": "order.placed"}
        await publisher.publish(event, routing_key="order.placed")

        mock_broker.publish.assert_called_once_with(
            message=event,
            exchange=publisher._default_exchange,
            routing_key="order.placed",
        )

    @pytest.mark.asyncio
    async def test_publish_derives_routing_key_from_event_type(self) -> None:
        """Publisher uses event_type as routing key if not provided."""
        mock_broker = MagicMock()
        mock_broker.publish = AsyncMock()

        publisher = RabbitEventPublisher(broker=mock_broker)

        event = {"event_id": "789", "event_type": "payment.processed"}
        await publisher.publish(event)

        mock_broker.publish.assert_called_once()
        call_args = mock_broker.publish.call_args
        assert call_args.kwargs["routing_key"] == "payment.processed"

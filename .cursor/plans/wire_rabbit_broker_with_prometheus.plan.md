# Wire RabbitMQ Broker with RabbitPrometheusMiddleware

## Overview

Complete the RabbitMQ broker infrastructure to enable the Kafka→RabbitMQ bridge (Feature 8 from initial plan). This includes creating the broker factory with middleware stacking, RabbitMQ publisher, bridge consumer wiring, and comprehensive tests.

**Status:** The `RabbitPrometheusMiddleware` class exists but is not wired to any broker. The bridge consumer logic exists but lacks the RabbitMQ publisher and broker infrastructure.

## Current state

**What exists:**
- ✅ `RabbitPrometheusMiddleware` class ([src/messaging/infrastructure/pubsub/rabbit_prometheus_middleware.py](src/messaging/infrastructure/pubsub/rabbit_prometheus_middleware.py))
- ✅ `BridgeConsumer` class skeleton ([src/messaging/infrastructure/pubsub/bridge/consumer.py](src/messaging/infrastructure/pubsub/bridge/consumer.py))
- ✅ Bridge configuration and routing ([src/messaging/infrastructure/pubsub/bridge/config.py](src/messaging/infrastructure/pubsub/bridge/config.py), [src/messaging/infrastructure/pubsub/bridge/routing_key_builder.py](src/messaging/infrastructure/pubsub/bridge/routing_key_builder.py))
- ✅ Integration test stubs ([tests/integration/test_kafka_rabbitmq_bridge.py](tests/integration/test_kafka_rabbitmq_bridge.py))

**What's missing:**
- ❌ `create_rabbit_broker()` factory function (analogous to `create_kafka_broker()`)
- ❌ RabbitMQ settings in `Settings` class (connection URL, exchange, etc.)
- ❌ `RabbitEventPublisher` implementation
- ❌ RabbitMQ broker instantiation in `main.py` lifespan
- ❌ Bridge consumer wiring to both brokers
- ❌ Functional integration tests (current tests are placeholders)

## Architecture goal

Following the initial plan's data flow (lines 182-197):

```
Kafka → Bridge Consumer (idempotent) → Rate Limiter → Circuit Breaker → 
OTel Middleware → RabbitPrometheusMiddleware → RabbitMQ Publisher → RabbitMQ Exchange
```

The RabbitMQ broker should use the same middleware stacking pattern as the Kafka broker:
1. **CircuitBreakerMiddleware** (resilience)
2. **RateLimiterMiddleware** (optional, for outbound rate control)
3. **RabbitPrometheusMiddleware** (metrics)
4. **TelemetryMiddleware** (OTel tracing, shared with Kafka broker)

## Serena MCP requirement

**CRITICAL**: When referencing or modifying existing code symbols, use Serena MCP to verify signatures and extract code structures. This applies to:

- `IdempotentConsumerBase` (for bridge consumer base class)
- `SqlAlchemyProcessedMessageStore` (for message deduplication)
- `CircuitBreakerMiddleware` (for resilience middleware)
- `RateLimiterMiddleware` (for rate limiting middleware)
- `RabbitPrometheusMiddleware` (verifying existing middleware implementation)
- `create_kafka_broker()` (as template for RabbitMQ broker factory)
- `KafkaEventPublisher` (as template for RabbitMQ publisher)
- `BridgeConsumer` (for updating existing bridge logic)
- Any other existing classes, methods, or fixtures

**Do not guess at class/method signatures.** If Serena MCP is not working, ask the user to enable it before proceeding with implementation.

## Phase 1: Add RabbitMQ configuration settings

### Modify `src/messaging/config.py`

Add RabbitMQ connection and operational settings:

```python
# RabbitMQ configuration
rabbitmq_url: str = Field(
    default="amqp://guest:guest@localhost:5672//",
    description="RabbitMQ connection URL (AMQP protocol)",
)
rabbitmq_exchange: str = Field(
    default="events",
    description="Default RabbitMQ exchange for publishing events",
)
rabbitmq_exchange_type: str = Field(
    default="topic",
    description="RabbitMQ exchange type (topic, direct, fanout, headers)",
)
rabbitmq_exchange_durable: bool = Field(
    default=True,
    description="Whether the RabbitMQ exchange should be durable",
)
rabbitmq_publisher_confirms: bool = Field(
    default=True,
    description="Enable RabbitMQ publisher confirms for reliability",
)

# RabbitMQ rate limiting (optional, uses RateLimiterMiddleware)
rabbitmq_rate_limit: int = Field(
    default=500,
    description="Max RabbitMQ messages per interval",
)
rabbitmq_rate_interval: float = Field(
    default=60.0,
    description="RabbitMQ rate window seconds",
)
rabbitmq_rate_limiter_enabled: bool = Field(
    default=False,
    description="Enable rate limiting middleware for RabbitMQ consumption",
)
```

### Test

**File:** `tests/unit/test_config.py` (add to existing file)

```python
def test_rabbitmq_settings_defaults() -> None:
    """RabbitMQ settings have correct defaults."""
    settings = Settings()
    assert settings.rabbitmq_url == "amqp://guest:guest@localhost:5672//"
    assert settings.rabbitmq_exchange == "events"
    assert settings.rabbitmq_exchange_type == "topic"
    assert settings.rabbitmq_publisher_confirms is True
    assert settings.rabbitmq_rate_limiter_enabled is False
```

## Phase 2: Create RabbitMQ broker factory

### Create `src/messaging/infrastructure/pubsub/rabbit_broker_config.py`

New file (under 100 lines):

```python
"""RabbitMQ broker factory with middleware stacking."""

from typing import Any

from faststream.rabbit import RabbitBroker
from prometheus_client import CollectorRegistry

from messaging.config import Settings
from messaging.infrastructure.pubsub.rabbit_prometheus_middleware import (
    RabbitPrometheusMiddleware,
)
from messaging.infrastructure.resilience.circuit_breaker_middleware import (
    CircuitBreakerMiddleware,
)
from messaging.infrastructure.resilience.rate_limiter_middleware import (
    RateLimiterMiddleware,
)


def create_rabbit_broker(
    settings: Settings,
    prometheus_registry: CollectorRegistry | None = None,
    tracer_provider: Any | None = None,
    enable_rate_limiter: bool = False,
    rate_limit_max_rate: int = 500,
    rate_limit_time_period: float = 60.0,
) -> RabbitBroker:
    """Create RabbitMQ broker with middleware stack.

    Middleware order (innermost to outermost):
    1. CircuitBreakerMiddleware (resilience)
    2. RateLimiterMiddleware (optional, resilience)
    3. RabbitPrometheusMiddleware (metrics)
    4. TelemetryMiddleware (OTel, added externally)

    Args:
        settings: Application settings with RabbitMQ connection config.
        prometheus_registry: Optional Prometheus registry for metrics.
        tracer_provider: Optional OpenTelemetry tracer provider.
        enable_rate_limiter: Whether to add rate limiter middleware.
        rate_limit_max_rate: Maximum messages per time period.
        rate_limit_time_period: Time period in seconds for rate limiting.

    Returns:
        Configured RabbitBroker instance with middleware stack.
    """
    middlewares: list[Any] = []

    # Add Circuit Breaker middleware (innermost)
    middlewares.append(
        CircuitBreakerMiddleware(
            failure_threshold=5,
            reset_timeout=30.0,
        )
    )

    # Add Rate Limiter middleware if enabled
    if enable_rate_limiter:
        middlewares.append(
            RateLimiterMiddleware(
                max_rate=rate_limit_max_rate,
                time_period=rate_limit_time_period,
            )
        )

    # Add Prometheus middleware
    middlewares.append(
        RabbitPrometheusMiddleware(
            registry=prometheus_registry,
        )
    )

    # Note: TelemetryMiddleware is added in main.py via
    # FastStreamInstrumentator().instrument() for all brokers

    broker = RabbitBroker(
        url=settings.rabbitmq_url,
        max_consumers=10,
        # graceful_timeout=5,  # Graceful shutdown timeout
        middlewares=middlewares,
    )

    return broker
```

### Tests

**File:** `tests/unit/infrastructure/test_rabbit_broker_config.py` (new file, under 100 lines)

```python
"""Unit tests for RabbitMQ broker configuration and middleware wiring."""

import pytest
from prometheus_client import CollectorRegistry

from messaging.config import Settings
from messaging.infrastructure.pubsub.rabbit_broker_config import create_rabbit_broker
from messaging.infrastructure.resilience.rate_limiter_middleware import (
    RateLimiterMiddleware,
)


class TestCreateRabbitBroker:
    """Test RabbitMQ broker middleware configuration."""

    def test_broker_without_rate_limiter_has_two_middlewares(self) -> None:
        """Broker has 2 middlewares when rate limiter disabled."""
        settings = Settings(
            rabbitmq_url="amqp://guest:guest@localhost:5672//",
            rabbitmq_rate_limiter_enabled=False,
        )
        registry = CollectorRegistry()

        broker = create_rabbit_broker(
            settings,
            prometheus_registry=registry,
            enable_rate_limiter=False,
        )

        # Circuit breaker + Prometheus (no Telemetry since no tracer)
        assert len(broker.middlewares) == 2

    def test_broker_with_rate_limiter_has_three_middlewares(self) -> None:
        """Broker has 3 middlewares when rate limiter enabled."""
        settings = Settings(
            rabbitmq_url="amqp://guest:guest@localhost:5672//",
            rabbitmq_rate_limiter_enabled=True,
            rabbitmq_rate_limit=100,
            rabbitmq_rate_interval=1.0,
        )
        registry = CollectorRegistry()

        broker = create_rabbit_broker(
            settings,
            prometheus_registry=registry,
            enable_rate_limiter=True,
            rate_limit_max_rate=100,
            rate_limit_time_period=1.0,
        )

        # Circuit breaker + Rate limiter + Prometheus
        assert len(broker.middlewares) == 3

    def test_rate_limiter_middleware_is_second_in_stack(self) -> None:
        """Rate limiter comes after circuit breaker in middleware stack."""
        settings = Settings(
            rabbitmq_url="amqp://guest:guest@localhost:5672//",
        )

        broker = create_rabbit_broker(
            settings,
            enable_rate_limiter=True,
            rate_limit_max_rate=50,
            rate_limit_time_period=2.0,
        )

        # middlewares[0] = circuit breaker factory
        # middlewares[1] = rate limiter instance
        assert len(broker.middlewares) >= 2
        rate_limiter = broker.middlewares[1]
        assert isinstance(rate_limiter, RateLimiterMiddleware)
        assert rate_limiter._limiter.max_rate == 50
        assert rate_limiter._limiter.time_period == 2.0
```

## Phase 3: Create RabbitMQ publisher

### Create `src/messaging/infrastructure/pubsub/rabbit/publisher.py`

New file (under 100 lines):

```python
"""RabbitMQ event publisher using FastStream RabbitBroker."""

from typing import Any

from faststream.rabbit import RabbitBroker

from messaging.core.contracts.events import BaseEvent


class RabbitEventPublisher:
    """Publishes events to RabbitMQ exchanges with routing keys."""

    def __init__(
        self,
        broker: RabbitBroker,
        default_exchange: str = "events",
    ) -> None:
        """Initialize RabbitMQ publisher.

        Args:
            broker: FastStream RabbitBroker instance.
            default_exchange: Default exchange for publishing events.
        """
        self._broker = broker
        self._default_exchange = default_exchange

    async def publish_to_exchange(
        self,
        event: BaseEvent | dict[str, Any],
        routing_key: str,
        exchange: str | None = None,
    ) -> None:
        """Publish event to RabbitMQ exchange with routing key.

        Args:
            event: Event to publish (BaseEvent or dict).
            routing_key: Routing key for message routing.
            exchange: Optional exchange override (defaults to default_exchange).
        """
        target_exchange = exchange or self._default_exchange

        # Convert BaseEvent to dict if needed
        payload = event.model_dump() if isinstance(event, BaseEvent) else event

        await self._broker.publish(
            message=payload,
            exchange=target_exchange,
            routing_key=routing_key,
        )

    async def publish(
        self,
        event: BaseEvent | dict[str, Any],
        routing_key: str | None = None,
    ) -> None:
        """Publish event to default exchange.

        Args:
            event: Event to publish.
            routing_key: Optional routing key (defaults to event type).
        """
        # Use event type as routing key if not specified
        if routing_key is None:
            if isinstance(event, BaseEvent):
                routing_key = event.event_type
            else:
                routing_key = event.get("event_type", "unknown")

        await self.publish_to_exchange(event, routing_key)
```

### Tests

**File:** `tests/unit/infrastructure/test_rabbit_publisher.py` (new file, under 100 lines)

```python
"""Unit tests for RabbitMQ event publisher."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from messaging.core.contracts.events import BaseEvent
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
            exchange="default-events",
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
```

## Phase 4: Wire RabbitMQ broker into main.py

### Modify `src/messaging/main.py`

Update the `lifespan()` context manager to instantiate the RabbitMQ broker alongside the Kafka broker.

**Changes:**

1. Import `create_rabbit_broker` and `RabbitEventPublisher`
2. Create RabbitMQ broker in lifespan with same middleware pattern as Kafka
3. Pass shared `prometheus_registry` to both brokers
4. Start RabbitMQ broker after Kafka broker
5. Expose `rabbit_broker` via `app.state` for potential use in routes

```python
from messaging.infrastructure.pubsub.rabbit_broker_config import create_rabbit_broker
from messaging.infrastructure.pubsub.rabbit.publisher import RabbitEventPublisher

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifecycle: startup and shutdown."""
    settings: Settings = app.state.settings
    db_engine = app.state.db_engine
    prometheus_registry = app.state.prometheus_registry

    # ... (existing Kafka broker setup)

    # Create RabbitMQ broker with middleware stack
    rabbit_broker = create_rabbit_broker(
        settings,
        prometheus_registry=prometheus_registry,
        enable_rate_limiter=settings.rabbitmq_rate_limiter_enabled,
        rate_limit_max_rate=settings.rabbitmq_rate_limit,
        rate_limit_time_period=settings.rabbitmq_rate_interval,
    )

    # Start RabbitMQ broker
    await rabbit_broker.start()

    # Create RabbitMQ publisher
    rabbit_publisher = RabbitEventPublisher(
        broker=rabbit_broker,
        default_exchange=settings.rabbitmq_exchange,
    )

    # Store in app.state for access in routes/consumers
    app.state.rabbit_broker = rabbit_broker
    app.state.rabbit_publisher = rabbit_publisher

    # ... (existing EventBus and outbox worker setup)

    try:
        yield
    finally:
        # Shutdown RabbitMQ broker
        await rabbit_broker.close()

        # ... (existing cleanup)
```

### Tests

**File:** `tests/integration/test_main_lifespan.py` (add to existing file)

```python
@pytest.mark.asyncio
async def test_lifespan_initializes_rabbit_broker(
    app: FastAPI, rabbitmq_container
) -> None:
    """Application lifespan creates and starts RabbitMQ broker."""
    async with lifespan(app):
        assert hasattr(app.state, "rabbit_broker")
        assert hasattr(app.state, "rabbit_publisher")
        assert app.state.rabbit_broker is not None
        assert app.state.rabbit_publisher is not None
```

## Phase 5: Wire bridge consumer (Kafka→RabbitMQ)

### Modify `src/messaging/infrastructure/pubsub/bridge/consumer.py`

Update the `BridgeConsumer` to:
1. Accept `RabbitEventPublisher` in constructor
2. Implement message handling with routing key logic
3. Use idempotent consumer base for duplicate prevention

**Changes:**

```python
"""Kafka-to-RabbitMQ bridge consumer."""

from typing import Any

from messaging.core.contracts.events import BaseEvent
from messaging.infrastructure.consumers.idempotent_consumer_base import (
    IdempotentConsumerBase,
)
from messaging.infrastructure.pubsub.bridge.routing_key_builder import (
    build_routing_key,
)
from messaging.infrastructure.pubsub.rabbit.publisher import RabbitEventPublisher


class BridgeConsumer(IdempotentConsumerBase):
    """Consume from Kafka, route to RabbitMQ with idempotency."""

    def __init__(
        self,
        processed_message_store: Any,  # IProcessedMessageStore
        rabbit_publisher: RabbitEventPublisher,
        routing_key_template: str = "{event_type}",
    ) -> None:
        """Initialize bridge consumer.

        Args:
            processed_message_store: Store for tracking processed messages.
            rabbit_publisher: RabbitMQ publisher for forwarding events.
            routing_key_template: Template for building routing keys.
        """
        super().__init__(processed_message_store)
        self._rabbit_publisher = rabbit_publisher
        self._routing_key_template = routing_key_template

    async def handle_message(self, message: dict[str, Any]) -> None:
        """Handle Kafka message by routing to RabbitMQ.

        Args:
            message: Event message from Kafka (already deserialized).
        """
        # Build routing key from event data
        routing_key = build_routing_key(self._routing_key_template, message)

        # Publish to RabbitMQ
        await self._rabbit_publisher.publish_to_exchange(
            event=message,
            routing_key=routing_key,
        )
```

### Wire bridge in main.py

Add bridge consumer instantiation and subscription:

```python
from messaging.infrastructure.pubsub.bridge.consumer import BridgeConsumer
from messaging.infrastructure.pubsub.bridge.config import BridgeConfig

# ... in lifespan():

# Create bridge consumer
bridge_config = BridgeConfig(
    kafka_topic="events",
    rabbitmq_exchange=settings.rabbitmq_exchange,
    routing_key_template="{event_type}",
)

bridge_consumer = BridgeConsumer(
    processed_message_store=processed_message_store,
    rabbit_publisher=rabbit_publisher,
    routing_key_template=bridge_config.routing_key_template,
)

# Subscribe bridge consumer to Kafka topic
@kafka_broker.subscriber(bridge_config.kafka_topic)
async def handle_kafka_event(message: dict) -> None:
    """Bridge handler: consume from Kafka, forward to RabbitMQ."""
    await bridge_consumer.consume(message)
```

### Tests

**File:** `tests/integration/test_kafka_rabbitmq_bridge.py` (update placeholders)

Update the existing placeholder tests to verify:
1. Bridge consumes from Kafka
2. Bridge publishes to RabbitMQ with correct routing key
3. Bridge is idempotent (prevents duplicate publishes)
4. Bridge handles malformed messages gracefully

```python
@pytest.mark.asyncio
async def test_bridge_publishes_to_rabbitmq(
    kafka_container, rabbitmq_container, async_client_with_kafka
) -> None:
    """Bridge publishes consumed Kafka events to RabbitMQ with routing key."""
    from confluent_kafka import Producer
    import aio_pika

    # Publish to Kafka
    producer_config = {
        "bootstrap.servers": kafka_container.get_bootstrap_server(),
    }
    producer = Producer(producer_config)

    test_message = {"event_id": "bridge-test-2", "event_type": "user.created"}
    producer.produce(
        "events",
        key=b"user-123",
        value=json.dumps(test_message).encode(),
    )
    producer.flush()

    # Connect to RabbitMQ and verify message arrived
    rabbitmq_url = (
        f"amqp://{rabbitmq_container.username}:{rabbitmq_container.password}"
        f"@{rabbitmq_container.get_container_host_ip()}"
        f":{rabbitmq_container.get_exposed_port(5672)}//"
    )

    connection = await aio_pika.connect_robust(rabbitmq_url)
    channel = await connection.channel()

    # Declare queue and bind to exchange
    exchange = await channel.declare_exchange("events", type="topic", durable=True)
    queue = await channel.declare_queue("test-queue", auto_delete=True)
    await queue.bind(exchange, routing_key="user.created")

    await asyncio.sleep(2)  # Give bridge time to process

    # Verify queue received message
    message = await queue.get(timeout=5)
    assert message is not None
    body = json.loads(message.body.decode())
    assert body["event_id"] == "bridge-test-2"
    assert body["event_type"] == "user.created"

    await connection.close()
```

## Phase 6: Update documentation

### Update README.md architecture diagram

The RabbitMQ broker is already shown in the diagram (lines 220-226 in the initial plan's diagram). Verify that the middleware stack matches the implementation:

```text
│    │  ┌────────────────────────────────────────────────┐ │
│    │  │  MIDDLEWARE STACK (RabbitMQ broker)            │ │
│    │  │  • CircuitBreakerMiddleware (resilience)       │ │
│    │  │  • RateLimiterMiddleware (optional, disabled)  │ │
│    │  │  • RabbitPrometheusMiddleware (metrics)        │ │
│    │  │  • TelemetryMiddleware (OTel, shared)          │ │
│    │  └────────────────────────────────────────────────┘ │
```

## Execution checklist

- [ ] Phase 1: Add RabbitMQ settings to `config.py` + test
- [ ] Phase 2: Create `rabbit_broker_config.py` + tests
- [ ] Phase 3: Create `rabbit/publisher.py` + tests
- [ ] Phase 4: Wire RabbitMQ broker into `main.py` + integration test
- [ ] Phase 5: Wire bridge consumer in `main.py` + update integration tests
- [ ] Phase 6: Update README.md to reflect RabbitMQ middleware stack
- [ ] Run all linters and tests to verify everything passes

## Files to create/modify

| File | Action | Lines (est.) |
|------|--------|--------------|
| `src/messaging/config.py` | Add RabbitMQ settings | +40 |
| `src/messaging/infrastructure/pubsub/rabbit_broker_config.py` | Create factory | +90 |
| `src/messaging/infrastructure/pubsub/rabbit/publisher.py` | Create publisher | +70 |
| `src/messaging/infrastructure/pubsub/bridge/consumer.py` | Update with RabbitMQ publisher | +30 |
| `src/messaging/main.py` | Wire RabbitMQ broker and bridge | +40 |
| `tests/unit/test_config.py` | Add RabbitMQ settings test | +10 |
| `tests/unit/infrastructure/test_rabbit_broker_config.py` | Create broker factory tests | +90 |
| `tests/unit/infrastructure/test_rabbit_publisher.py` | Create publisher tests | +80 |
| `tests/integration/test_main_lifespan.py` | Add RabbitMQ broker lifecycle test | +15 |
| `tests/integration/test_kafka_rabbitmq_bridge.py` | Update placeholders | +50 |

**Total estimated LOC:** ~515 lines across 10 files

## Dependencies

This plan depends on:
- ✅ `CircuitBreakerMiddleware` (already implemented)
- ✅ `RateLimiterMiddleware` (already implemented)
- ✅ `RabbitPrometheusMiddleware` (already implemented)
- ✅ `IdempotentConsumerBase` (already implemented)
- ✅ `SqlAlchemyProcessedMessageStore` (already implemented)
- ✅ Bridge routing logic (already implemented)

No new dependencies required. This plan completes the wiring of existing components.

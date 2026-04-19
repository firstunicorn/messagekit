"""RabbitMQ broker factory implementation."""

from typing import Any

from faststream.rabbit import RabbitBroker
from faststream.rabbit.opentelemetry import RabbitTelemetryMiddleware
from opentelemetry import trace
from prometheus_client import CollectorRegistry

from messagekit.config import Settings
from messagekit.core.contracts.circuit_breaker import CircuitBreaker
from messagekit.infrastructure.pubsub.rabbit_broker_config._factory_helpers import (
    create_circuit_breaker_factory,
)
from messagekit.infrastructure.pubsub.rabbit_prometheus_middleware import RabbitPrometheusMiddleware
from messagekit.infrastructure.resilience.rate_limiter_middleware import RateLimiterMiddleware


def create_rabbit_broker(
    settings: Settings,
    prometheus_registry: CollectorRegistry | None = None,
    tracer_provider: trace.TracerProvider | None = None,
    circuit_breaker_threshold: int = 5,
    circuit_breaker_timeout: float = 30.0,
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
        circuit_breaker_threshold: Number of failures before circuit opens (default: 5)
        circuit_breaker_timeout: Seconds before half-open state (default: 30.0)
        enable_rate_limiter: Whether to add rate limiter middleware.
        rate_limit_max_rate: Maximum messages per time period.
        rate_limit_time_period: Time period in seconds for rate limiting.

    Returns:
        Configured RabbitBroker instance with middleware stack.
    """
    middlewares: list[Any] = []

    shared_breaker = CircuitBreaker(
        failure_threshold=circuit_breaker_threshold,
        reset_timeout=circuit_breaker_timeout,
    )

    circuit_breaker_factory = create_circuit_breaker_factory(
        shared_breaker=shared_breaker,
        circuit_breaker_threshold=circuit_breaker_threshold,
        circuit_breaker_timeout=circuit_breaker_timeout,
    )
    middlewares.append(circuit_breaker_factory)

    if enable_rate_limiter:
        middlewares.append(
            RateLimiterMiddleware(
                max_rate=rate_limit_max_rate,
                time_period=rate_limit_time_period,
            )
        )

    if prometheus_registry is not None:
        middlewares.append(
            RabbitPrometheusMiddleware(
                registry=prometheus_registry,
            )
        )

    if tracer_provider is not None:
        middlewares.append(
            RabbitTelemetryMiddleware(
                tracer_provider=tracer_provider,
            )
        )

    return RabbitBroker(
        url=settings.rabbitmq_url,
        middlewares=middlewares,
    )

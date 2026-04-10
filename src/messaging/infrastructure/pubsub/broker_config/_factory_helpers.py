"""Circuit breaker factory helpers for Kafka broker."""

from collections.abc import Callable
from typing import Any

from messaging.core.contracts.circuit_breaker import CircuitBreaker
from messaging.infrastructure.resilience.circuit_breaker_middleware import CircuitBreakerMiddleware


def create_circuit_breaker_factory(
    shared_breaker: CircuitBreaker,
    circuit_breaker_threshold: int,
    circuit_breaker_timeout: float,
) -> Callable[[Any, Any], CircuitBreakerMiddleware]:
    """Create circuit breaker factory for FastStream middleware.

    Args:
        shared_breaker: Shared circuit breaker instance.
        circuit_breaker_threshold: Number of failures before circuit opens.
        circuit_breaker_timeout: Seconds before half-open state.

    Returns:
        Factory function that creates CircuitBreakerMiddleware with shared breaker.
    """
    def circuit_breaker_factory(msg: Any = None, context: Any = None) -> CircuitBreakerMiddleware:  # noqa: ARG001
        # Parameters required by FastStream middleware interface but unused
        middleware = CircuitBreakerMiddleware(
            failure_threshold=circuit_breaker_threshold,
            reset_timeout=circuit_breaker_timeout,
        )
        middleware._breaker = shared_breaker
        return middleware

    return circuit_breaker_factory

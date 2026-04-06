"""Factory for the FastStream Kafka broker.

This module provides `create_kafka_broker`, a utility that builds and configures
a FastStream `KafkaBroker` instance using the application settings with native
observability middlewares (Prometheus, OpenTelemetry).

See Also
--------
- messaging.config.Settings : The application settings
- messaging.infrastructure.pubsub.kafka_publisher : The publisher that uses this broker
"""

# mypy: disable-error-code="no-any-unimported,arg-type"

from typing import Any

from faststream.kafka import KafkaBroker
from faststream.kafka.opentelemetry import KafkaTelemetryMiddleware
from faststream.kafka.prometheus import KafkaPrometheusMiddleware
from opentelemetry import trace
from prometheus_client import CollectorRegistry

from messaging.config import Settings


def create_kafka_broker(
    settings: Settings,
    prometheus_registry: CollectorRegistry | None = None,
    tracer_provider: trace.TracerProvider | None = None,
) -> KafkaBroker:
    """Create a Kafka broker configured with native observability middlewares.

    Args:
        settings: Application settings
        prometheus_registry: Optional Prometheus registry for metrics
        tracer_provider: Optional OpenTelemetry tracer provider for tracing

    Returns:
        KafkaBroker: Configured FastStream Kafka broker with middlewares
    """
    middlewares: list[Any] = []

    # Add Prometheus middleware if registry provided
    if prometheus_registry is not None:
        middlewares.append(
            KafkaPrometheusMiddleware(
                registry=prometheus_registry,
                app_name=settings.service_name,
            )
        )

    # Add OpenTelemetry middleware if tracer provider provided
    if tracer_provider is not None:
        middlewares.append(
            KafkaTelemetryMiddleware(
                tracer_provider=tracer_provider,
            )
        )

    if middlewares:
        return KafkaBroker(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            client_id=settings.kafka_client_id,
            enable_idempotence=True,
            middlewares=middlewares,
        )
    return KafkaBroker(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        client_id=settings.kafka_client_id,
        enable_idempotence=True,
    )

"""Factory for the FastStream Kafka broker using Confluent backend.

IMPORTANT: This uses faststream[confluent], which wraps the open-source
confluent-kafka-python library (Apache 2.0 licensed). This is NOT the proprietary
Confluent Platform.

See Also
--------
- messaging.config.Settings : The application settings
- messaging.infrastructure.pubsub.kafka_publisher : The publisher that uses this broker
- confluent-kafka-python: https://github.com/confluentinc/confluent-kafka-python
"""

from messagekit.infrastructure.pubsub.broker_config.factory import create_kafka_broker

__all__ = ["create_kafka_broker"]

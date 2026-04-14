# Kafka topic isolation per test

**[Rule](#rule)** • **[Why](#why)** • **[Pattern](#pattern)** • **[Prevention](#prevention)**

## Rule

Integration tests sharing Kafka infrastructure MUST use unique topic names per test, NOT just unique consumer groups.

## Why consumer groups alone fail

Even with unique consumer groups, shared topic causes issues:

1. Consumer group "test-A" reads from topic "events"
2. Consumer group "test-B" also reads from topic "events" (different group, SAME topic)
3. Both groups see ALL messages in topic "events"
4. New consumer groups start from earliest/latest offset
5. If configured for earliest: test-B sees test-A's messages

**Kafka architecture**:
- Topic = actual message store
- Consumer group = offset tracking mechanism
- Multiple groups can read same topic independently
- But they ALL see ALL messages in that topic

## Why this matters

```python
# Test A publishes
producer.produce("events", message_A)

# Test B with different consumer group
# Still reads from SAME topic "events"
# Receives message_A + message_B (contaminated!)
```

**Real error**:
```
AssertionError: assert 1 == 2
  where 2 = len([message_from_test_A, message_from_test_B])
```

## Pattern

**Setup helper must accept kafka_topic parameter**:

```python
def setup_test_containers_config(
    kafka_container,
    rabbitmq_container,
    monkeypatch,
    kafka_topic: str = "events",  # REQUIRED PARAMETER
    exchange: str = "test-events",
    consumer_group_id: str = "test",
) -> tuple[str, str, str]:
    """Configure with unique identifiers per test."""
    kafka_bootstrap = kafka_container.get_bootstrap_server()
    rabbitmq_url = rabbitmq_container.get_connection_url()
    
    monkeypatch.setattr(settings, "kafka_bootstrap_servers", kafka_bootstrap)
    monkeypatch.setattr(settings, "rabbitmq_url", rabbitmq_url)
    monkeypatch.setattr(settings, "rabbitmq_exchange", exchange)
    
    return kafka_bootstrap, rabbitmq_url, consumer_group_id


def initialize_production_bridge(
    session_factory,
    consumer_group_id: str = "test",
    kafka_topic: str = "events",  # REQUIRED PARAMETER
) -> tuple[Any, Any]:
    """Initialize bridge with configurable topic."""
    broker, rabbit_broker, rabbit_publisher = initialize_brokers_and_publishers()
    bridge_config = BridgeConfig(
        kafka_topic=kafka_topic,  # Use parameter
        rabbitmq_exchange=settings.rabbitmq_exchange,
        routing_key_template="{event_type}",
        consumer_group_id=consumer_group_id,
    )
    register_bridge_handler(broker, bridge_config, rabbit_publisher, session_factory)
    return broker, rabbit_broker
```

**Per-test usage**:

```python
@pytest.mark.integration
@pytest.mark.requires_kafka
class TestIdempotency:
    async def test_prevents_duplicates(self, ...):
        # UNIQUE topic AND consumer group
        kafka_url, _, group_id = setup_test_containers_config(
            kafka_container,
            rabbitmq_container,
            monkeypatch,
            kafka_topic="events-idempotency-test",  # UNIQUE TOPIC
            consumer_group_id=f"idempotency-{uuid4()}"  # UNIQUE GROUP
        )
        
        broker, rabbit_broker = initialize_production_bridge(
            async_session_factory,
            consumer_group_id=group_id,
            kafka_topic="events-idempotency-test",  # Pass through
        )
        
        # Publish to UNIQUE topic
        producer.produce("events-idempotency-test", message)
```

**Different test uses different topic**:

```python
@pytest.mark.integration
class TestExceptionHandling:
    async def test_nack_behavior(self, ...):
        # DIFFERENT topic AND consumer group
        kafka_url, _, group_id = setup_test_containers_config(
            kafka_container,
            rabbitmq_container,
            monkeypatch,
            kafka_topic="events-exception-test",  # DIFFERENT TOPIC
            consumer_group_id=f"exception-{uuid4()}"  # DIFFERENT GROUP
        )
        
        broker, rabbit_broker = initialize_production_bridge(
            async_session_factory,
            consumer_group_id=group_id,
            kafka_topic="events-exception-test",  # Different
        )
        
        # Publish to DIFFERENT topic
        producer.produce("events-exception-test", message)
```

## Prevention

**Checklist for new Kafka integration tests**:
- [ ] Unique kafka_topic passed to setup helper
- [ ] Unique consumer_group_id passed to setup helper
- [ ] Producer uses same unique topic name
- [ ] Bridge config uses same unique topic name
- [ ] Test doesn't assume clean topic state

**Both are required**:
```python
# INCOMPLETE - will fail
kafka_topic="events",  # SHARED
consumer_group_id="unique-group"  # Unique but insufficient

# CORRECT - both unique
kafka_topic="events-my-test-unique",  # UNIQUE
consumer_group_id="my-test-unique-group"  # UNIQUE
```

## Related

- Consumer group isolation: kafka-consumer-group-test-isolation.md
- Full bug details: 2026-04-13-shared-kafka-topic-cross-contamination-bug.md
- General principles: test-isolation-principles.md

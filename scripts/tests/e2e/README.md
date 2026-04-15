# E2E tests for python-eventing

Real microservices architecture simulation testing the complete event flow.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Producer Service (producer_service.py)                      │
│                                                              │
│  EventBus.emit(TestEvent)                                   │
│         │                                                    │
│         ▼                                                    │
│  OutboxEventHandler                                         │
│         │                                                    │
│         ▼                                                    │
│  PostgreSQL outbox_events table                             │
│         │                                                    │
│         ▼                                                    │
│  KafkaEventPublisher (simulates CDC)                        │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────┐
              │   Kafka Broker   │
              │   Topic:         │
              │test.event_emitted│
              └──────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ Consumer Service (consumer_service.py)                      │
│                                                              │
│  @broker.subscriber("test.event_emitted")                   │
│         │                                                    │
│         ▼                                                    │
│  IdempotentConsumerBase pattern                             │
│         │                                                    │
│         ▼                                                    │
│  PostgreSQL processed_messages table                        │
│         │                                                    │
│         ▼                                                    │
│  Business logic (store event)                               │
└─────────────────────────────────────────────────────────────┘
```

## What it tests

1. **EventBus integration** - Event emission via EventBus
2. **Outbox pattern** - Atomic persistence to outbox table
3. **Kafka publishing** - Manual publishing from outbox (simulates CDC)
4. **Kafka consumption** - FastStream subscriber receives events
5. **Idempotency** - Duplicate messages are ignored via processed_message_store
6. **Database isolation** - Producer and consumer each have their own DB tables

## Prerequisites

### 1. Docker containers running

```powershell
# Start infrastructure
docker-compose up -d postgres kafka zookeeper

# Verify containers are healthy
docker-compose ps
```

### 2. Install dependencies

```powershell
# Already done if you ran poetry install
poetry install
```

## Running the tests

### Option 1: Using Python directly

```powershell
cd c:\coding\gridflow-microservices-codex-taskmaster\microservices\eventing
python scripts/tests/e2e/run_e2e_test.py
```

### Option 2: Using the shell script (recommended)

```powershell
cd c:\coding\gridflow-microservices-codex-taskmaster\microservices\eventing
.\scripts\tests\e2e\run_e2e.ps1
```

## Expected output

```
================================================================================
E2E TEST: Full event flow (EventBus + Outbox + Kafka + Consumer)
================================================================================

[STEP 1] Initializing services...
✅ Producer service started
✅ Consumer service started

[STEP 2] Emitting test event via EventBus...
✅ Event emitted: test.event_emitted (aggregate_id=test-aggregate-001)

[STEP 3] Verifying outbox persistence...
✅ Events in outbox: 1

[STEP 4] Publishing from outbox to Kafka (simulating CDC)...
✅ Events published to Kafka

[STEP 5] Waiting for consumer to receive event...

[STEP 6] Verifying consumer processed event...
✅ Received events: 1
✅ Processed messages in DB: 1

[STEP 7] Verifying event data...
✅ Event data verified correctly

[STEP 8] Testing idempotency (resending same event)...
✅ Received events after duplicate: 1
✅ Processed messages in DB: 1

================================================================================
✅ E2E TEST PASSED
================================================================================

Summary:
  • Events emitted: 1
  • Events in outbox: 1
  • Events received by consumer: 1
  • Processed messages (idempotent): 1
```

## What each file does

| File | Purpose |
|------|---------|
| `run_e2e_test.py` | Main test orchestrator - runs the full E2E flow |
| `producer_service.py` | Simulates producer microservice (EventBus + Outbox) |
| `consumer_service.py` | Simulates consumer microservice (Kafka + Idempotency) |
| `shared_events.py` | Shared event models (TestEvent) |
| `run_e2e.ps1` | PowerShell script to run tests easily |
| `README.md` | This file |

## Test flow breakdown

### Step 1: Initialize services
- Producer: Sets up EventBus with OutboxEventHandler
- Consumer: Sets up Kafka subscriber with idempotency store

### Step 2: Emit event
```python
event = TestEvent(
    aggregate_id="test-aggregate-001",
    user_id=12345,
    action="user_registered"
)
await producer.emit_event(event)
```

### Step 3: Verify outbox
- Checks `outbox_events` table has 1 record
- Verifies atomic write (business data + event)

### Step 4: Publish to Kafka
- Manually publishes from outbox (simulates CDC)
- In production, Kafka Connect does this automatically

### Step 5: Consumer receives
- FastStream subscriber picks up event from Kafka
- Idempotency check via `processed_messages` table

### Step 6: Verify consumption
- Checks event was received
- Checks `processed_messages` has 1 record

### Step 7: Verify data integrity
- Asserts event data matches what was emitted
- Validates `eventType`, `aggregateId`, `user_id`, `action`

### Step 8: Test idempotency
- Resends same event (simulates duplicate)
- Verifies consumer ignores duplicate (processed_messages count stays 1)

## Troubleshooting

### Error: Connection refused (Kafka)

**Cause:** Kafka container not running or not healthy.

**Fix:**
```powershell
docker-compose ps  # Check status
docker-compose up -d kafka zookeeper  # Restart if needed
docker-compose logs kafka  # Check logs
```

### Error: Connection refused (PostgreSQL)

**Cause:** PostgreSQL container not running.

**Fix:**
```powershell
docker-compose ps
docker-compose up -d postgres
docker-compose logs postgres
```

### Error: Table does not exist

**Cause:** Database tables not created.

**Fix:** Tables are created automatically by the test script. If issue persists, check migrations or create manually:

```powershell
poetry run alembic upgrade head
```

### Consumer not receiving events

**Cause:** Topic name mismatch or broker not connected.

**Fix:** 
1. Check Kafka topic exists:
   ```powershell
   docker exec eventing-kafka kafka-topics --list --bootstrap-server localhost:9092
   ```

2. Check consumer logs for errors in test output

### Idempotency test fails

**Cause:** Previous test runs left data in database.

**Fix:** Clean database:
```powershell
docker-compose down -v
docker-compose up -d
```

## Architecture notes

### Why simulate CDC?

In production, **Kafka Connect with Debezium CDC** watches the outbox table and automatically publishes events. For E2E tests, we manually publish to avoid requiring Kafka Connect setup.

### Database isolation

In a real microservices setup:
- Producer writes to `postgres-a:5432/service_a`
- Consumer writes to `postgres-b:5432/service_b`
- They communicate via Kafka (shared event bus)

For E2E simplicity, both use the same PostgreSQL database but maintain separate tables (`outbox_events` vs `processed_messages`), demonstrating the isolation pattern.

### EventBus vs direct outbox

This test uses **EventBus** (high-level API) which automatically calls OutboxEventHandler. You can also use the outbox repository directly:

```python
# EventBus approach (tested here)
await event_bus.emit(event)

# Direct outbox approach (also valid)
await outbox_repo.add_event(event, session)
```

Both achieve the same result: atomic persistence to outbox.

## Next steps

After E2E tests pass:

1. **Add CDC**: Set up Kafka Connect + Debezium for automatic publishing
2. **Add bridge**: Test RabbitMQ forwarding (Kafka → RabbitMQ)
3. **Multi-service**: Run multiple producers and consumers in parallel
4. **Chaos testing**: Kill containers mid-flow to test recovery
5. **Performance**: Measure throughput (events/second)

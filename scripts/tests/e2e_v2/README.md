# E2E V2 Tests - Separate Databases (Real-World Scenario)

Complete microservices simulation with database-per-service pattern.

## Architecture

```
┌──────────────────────────────────────┐
│ Producer Service                      │
│                                       │
│ Database: postgres-producer:5432      │
│   └── producer_db                     │
│       └── outbox_events table         │
│                                       │
│ EventBus.emit(TestEventV2)            │
│   ↓                                   │
│ OutboxEventHandler                    │
│   ↓                                   │
│ producer_db.outbox_events             │
└───────────────┬───────────────────────┘
                │
                ▼ publish (simulates CDC)
        ┌──────────────┐
        │    Kafka     │
        │ localhost:   │
        │    9093      │
        └──────┬───────┘
                │
                ▼ subscribe
┌──────────────────────────────────────┐
│ Consumer Service                      │
│                                       │
│ Database: postgres-consumer:5432      │
│   └── consumer_db                     │
│       └── processed_messages table    │
│                                       │
│ @broker.subscriber()                  │
│   ↓                                   │
│ IdempotentConsumerBase pattern        │
│   ↓                                   │
│ consumer_db.processed_messages        │
└───────────────────────────────────────┘
```

## Key differences from v1

| Aspect | V1 (Simple) | V2 (Real-World) |
|--------|-------------|-----------------|
| **Databases** | 1 shared (eventing) | 2 separate (producer_db, consumer_db) |
| **Postgres ports** | 5432 | 5433 (producer), 5434 (consumer) |
| **Kafka port** | 9092 | 9093 (isolated from main) |
| **Isolation test** | No | Yes (verifies no cross-contamination) |
| **Database per service** | No | Yes (true microservices pattern) |

## Prerequisites

### Docker must be running

```powershell
docker --version
docker-compose --version
```

### Python dependencies installed

```powershell
poetry install
```

## Running the test

### Option 1: PowerShell script (recommended)

```powershell
cd c:\coding\gridflow-microservices-codex-taskmaster\microservices\eventing\scripts\tests\e2e_v2
.\run_e2e_v2.ps1
```

This script:
1. Starts Docker containers (2 PostgreSQL + Kafka + Zookeeper)
2. Waits for health checks
3. Runs E2E test
4. Leaves containers running for inspection

### Option 2: Manual steps

```powershell
# 1. Start containers
cd c:\coding\gridflow-microservices-codex-taskmaster\microservices\eventing\scripts\tests\e2e_v2
docker-compose -f docker-compose.e2e.yml up -d

# 2. Wait for containers to be ready
Start-Sleep -Seconds 15

# 3. Run test
cd c:\coding\gridflow-microservices-codex-taskmaster\microservices\eventing
.venv\Scripts\python.exe scripts\tests\e2e_v2\run_e2e_test_v2.py
```

## Test flow

### Step 1: Initialize services
- Producer connects to `localhost:5433/producer_db`
- Consumer connects to `localhost:5434/consumer_db`
- Both create their own tables

### Step 2: Emit event
```python
event = TestEventV2(
    aggregate_id="test-agg-v2-001",
    user_id=98765,
    action="account_created"
)
await producer.emit_event(event)
```

### Step 3: Verify outbox (producer_db)
- Checks `producer_db.outbox_events` has 1 row
- Event persisted atomically

### Step 4: Publish to Kafka
- Manually publishes from outbox (simulates CDC)
- Event sent to Kafka topic: `test.event_emitted_v2`

### Step 5: Consumer receives
- FastStream subscriber receives from Kafka
- Writes to `consumer_db.processed_messages`

### Step 6: Verify consumption (consumer_db)
- Checks `consumer_db.processed_messages` has 1 row
- Event processed with idempotency

### Step 7: Verify database isolation
- ✅ `producer_db` has NO `processed_messages` table
- ✅ `consumer_db` has NO `outbox_events` table
- Confirms true database-per-service pattern

### Step 8: Test idempotency
- Republishes same event
- Consumer ignores duplicate (processed_messages stays at 1)

## Expected output

```
================================================================================
E2E TEST V2: Separate databases (database-per-service pattern)
================================================================================

[STEP 1] Initializing services with separate databases...
  Producer DB: postgres-producer:5432/producer_db
  Consumer DB: postgres-consumer:5432/consumer_db
✅ Producer service started (producer_db)
✅ Consumer service started (consumer_db)

[STEP 2] Emitting test event via EventBus...
✅ Event emitted to producer_db outbox

[STEP 3] Verifying outbox in producer_db...
✅ Events in producer_db outbox: 1

[STEP 4] Publishing from producer_db outbox to Kafka...
✅ Events published to Kafka (topic: test.event_emitted_v2)

[STEP 5] Waiting for consumer to receive from Kafka...

[STEP 6] Verifying consumer processed event in consumer_db...
✅ Consumer received events: 1
✅ Processed in consumer_db: 1

[STEP 7] Verifying database isolation...
  Checking producer_db has NO processed_messages...
  ✅ Producer DB has no processed_messages (correct isolation)
  Checking consumer_db has NO outbox_events...
  ✅ Consumer DB has no outbox_events (correct isolation)

[STEP 8] Testing idempotency...
  Received after duplicate: 1
  Processed count: 1

================================================================================
✅ E2E TEST V2 PASSED
================================================================================

Summary:
  • Producer DB: producer_db (outbox: 1)
  • Consumer DB: consumer_db (processed: 1)
  • Database isolation: ✅ Verified
  • Kafka communication: ✅ Working
  • Idempotency: ✅ Working
```

## Cleanup

### Stop containers (keep data)
```powershell
docker-compose -f docker-compose.e2e.yml down
```

### Stop and remove all data
```powershell
docker-compose -f docker-compose.e2e.yml down -v
```

### Inspect databases

**Producer database:**
```powershell
docker exec -it e2e-postgres-producer psql -U postgres -d producer_db -c "SELECT * FROM outbox_events;"
```

**Consumer database:**
```powershell
docker exec -it e2e-postgres-consumer psql -U postgres -d consumer_db -c "SELECT * FROM processed_messages;"
```

## Files

| File | Purpose | Lines |
|------|---------|-------|
| `docker-compose.e2e.yml` | Infrastructure definition | ~100 |
| `run_e2e_test_v2.py` | Main test orchestrator | ~150 |
| `producer_service_v2.py` | Producer microservice simulation | ~110 |
| `consumer_service_v2.py` | Consumer microservice simulation | ~110 |
| `shared_events_v2.py` | Shared event models | ~20 |
| `run_e2e_v2.ps1` | PowerShell runner | ~100 |
| `README.md` | This documentation | ~250 |

## Troubleshooting

### Containers won't start

Check logs:
```powershell
docker-compose -f docker-compose.e2e.yml logs
```

### Port conflicts

If ports 5433, 5434, or 9093 are in use, modify `docker-compose.e2e.yml`.

### Test hangs at Step 5

Consumer might not be receiving. Check:
1. Kafka topic exists: `docker exec e2e-kafka kafka-topics --list --bootstrap-server localhost:9093`
2. Producer published: Check producer logs
3. Consumer subscribed: Check consumer logs

### Database connection errors

Verify containers:
```powershell
docker ps | Select-String "e2e-postgres"
```

Verify databases exist:
```powershell
docker exec e2e-postgres-producer psql -U postgres -l
docker exec e2e-postgres-consumer psql -U postgres -l
```

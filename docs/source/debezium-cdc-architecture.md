# Debezium CDC architecture

**[Overview](#what-is-debezium)** • **[WAL-Based CDC](#how-debezium-works-wal-based-cdc)** • **[EventRouter SMT](#debezium-eventrouter-smt)** • **[Infrastructure Setup](#external-infrastructure-required)** • **[Performance](#performance-impact)**

## What is Debezium?

**Debezium** is a distributed platform for change data capture (CDC). It monitors your PostgreSQL database's **Write-Ahead Log (WAL)** and streams changes to Kafka in real-time.

**For the outbox pattern:**
- Application writes events to `outbox_event_record` table (transactional)
- Debezium detects the insert via PostgreSQL WAL
- EventRouter SMT transforms the outbox row into a proper Kafka message
- Event published to Kafka within milliseconds (<100ms)

---

## Outbox publishing: With vs without Debezium

### ❌ Without Debezium (polling worker - removed from codebase)

```python
# Custom Python worker (NO LONGER USED)
class ScheduledOutboxWorker:
    async def run(self):
        while True:
            await asyncio.sleep(5)  # Poll every 5 seconds
            events = await self.query_unpublished_events()
            for event in events:
                await self.kafka_publisher.publish(event)
                await self.mark_published(event)
```

**Problems:**
- ❌ **5-30 seconds latency** (polling interval)
- ❌ **High database load** (continuous `SELECT ... FOR UPDATE` queries)
- ❌ **Complex concurrency code** (Python async, error handling, retries)
- ❌ **Single-threaded bottleneck** (polling loop limits throughput)

### ✅ With Debezium CDC (current architecture)

```json
{
  "name": "outbox-connector",
  "config": {
    "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
    "database.hostname": "postgres",
    "database.dbname": "your_db",
    "table.include.list": "public.outbox_event_record",
    "plugin.name": "pgoutput",
    
    "transforms": "outbox",
    "transforms.outbox.type": "io.debezium.transforms.outbox.EventRouter",
    "transforms.outbox.table.field.event.id": "id",
    "transforms.outbox.table.field.event.key": "aggregate_id",
    "transforms.outbox.table.field.event.type": "event_type",
    "transforms.outbox.table.field.event.payload": "payload",
    "transforms.outbox.route.by.field": "event_type"
  }
}
```

**Advantages:**
- ✅ **Near-zero latency** (<100ms from commit to Kafka)
- ✅ **No database query load** (reads WAL only, not tables)
- ✅ **No custom code** (external infrastructure handles everything)
- ✅ **Horizontal scaling** (Kafka Connect cluster with multiple workers)
- ✅ **Automatic retries** (Kafka Connect handles failures)

---

## How Debezium works: WAL-based CDC

```text
Application Transaction:
┌─────────────────────────┐
│ BEGIN                   │
│ INSERT INTO users ...   │ ← Business data
│ INSERT INTO outbox ...  │ ← Event data
│ COMMIT                  │ ← Atomic!
└─────────────────────────┘
          ↓
PostgreSQL WAL (Write-Ahead Log):
┌─────────────────────────┐
│ LSN 1234: START TX      │
│ LSN 1235: users row     │
│ LSN 1236: outbox row    │ ← Debezium reads THIS
│ LSN 1237: COMMIT        │
└─────────────────────────┘
          ↓
Debezium EventRouter:
┌─────────────────────────┐
│ Parse outbox row        │
│ Extract: event_type →   │
│   Topic name            │
│ Extract: aggregate_id → │
│   Kafka key             │
│ Extract: payload →      │
│   Kafka value           │
│ Publish to Kafka        │
└─────────────────────────┘
          ↓
Kafka Topic:
┌─────────────────────────┐
│ Topic: user.created     │
│ Key: user-123           │
│ Value: {"userId": 123,  │
│         "email": "..."}│
└─────────────────────────┘
```

**Why WAL is powerful:**
- PostgreSQL writes ALL changes to WAL before tables (durability guarantee)
- Debezium tails WAL using logical replication (`pgoutput` plugin)
- Events published **immediately after COMMIT** (no polling delay)
- Zero impact on application queries (WAL is separate from table reads)

---

## Debezium EventRouter SMT

**SMT (Single Message Transform)** is Debezium's transformation engine. The **EventRouter** is specifically designed for the outbox pattern.

### Transformation example

```json
// Outbox table row:
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "aggregate_id": "user-123",
  "event_type": "user.created",
  "payload": "{\"userId\": 123, \"email\": \"user@example.com\", \"name\": \"John Doe\"}"
}

// EventRouter transforms to Kafka message:
Topic: user.created              ← From event_type field
Key: user-123                    ← From aggregate_id field
Value: {                         ← Unwrapped payload
  "userId": 123,
  "email": "user@example.com",
  "name": "John Doe"
}
Headers:
  id: 550e8400-e29b-41d4-a716-446655440000
```

### Configuration mapping

```json
"transforms.outbox.table.field.event.id": "id",              // → Kafka header
"transforms.outbox.table.field.event.key": "aggregate_id",   // → Kafka key (partition routing)
"transforms.outbox.table.field.event.type": "event_type",    // → Kafka topic name
"transforms.outbox.table.field.event.payload": "payload",    // → Kafka value (unwrapped)
"transforms.outbox.route.by.field": "event_type"             // Route to topic by this field
```

---

## External infrastructure required

**⚠️ This package does NOT provide:**
1. **Kafka Connect cluster** (separate JVM-based service)
2. **Debezium PostgreSQL connector plugin**
3. **Connector configuration and deployment**

### Docker Compose setup

```yaml
# docker-compose.yml (simplified)
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: your_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    command:
      - "postgres"
      - "-c"
      - "wal_level=logical"  # Enable WAL for CDC
  
  kafka:
    image: confluentinc/cp-kafka:latest
    environment:
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
  
  kafka-connect:
    image: debezium/connect:2.6
    environment:
      BOOTSTRAP_SERVERS: kafka:9092
      GROUP_ID: kafka-connect
      CONFIG_STORAGE_TOPIC: connect_configs
      OFFSET_STORAGE_TOPIC: connect_offsets
      STATUS_STORAGE_TOPIC: connect_status
    ports:
      - "8083:8083"
    depends_on:
      - kafka
      - postgres
```

### Register connector via REST API

```bash
curl -X POST http://kafka-connect:8083/connectors \
  -H "Content-Type: application/json" \
  -d '{
    "name": "outbox-connector",
    "config": {
      "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
      "database.hostname": "postgres",
      "database.port": "5432",
      "database.user": "postgres",
      "database.password": "postgres",
      "database.dbname": "your_db",
      "database.server.name": "your_service",
      "table.include.list": "public.outbox_event_record",
      "plugin.name": "pgoutput",
      "slot.name": "debezium_outbox",
      "publication.name": "debezium_publication",
      "transforms": "outbox",
      "transforms.outbox.type": "io.debezium.transforms.outbox.EventRouter",
      "transforms.outbox.table.field.event.id": "id",
      "transforms.outbox.table.field.event.key": "aggregate_id",
      "transforms.outbox.table.field.event.type": "event_type",
      "transforms.outbox.table.field.event.payload": "payload",
      "transforms.outbox.route.by.field": "event_type"
    }
  }'
```

### Verify connector status

```bash
# Check connector health
curl http://kafka-connect:8083/connectors/outbox-connector/status

# Expected response:
{
  "name": "outbox-connector",
  "connector": {
    "state": "RUNNING",
    "worker_id": "kafka-connect:8083"
  },
  "tasks": [
    {
      "id": 0,
      "state": "RUNNING",
      "worker_id": "kafka-connect:8083"
    }
  ]
}
```

---

## Performance impact

| Metric | Polling Worker | Debezium CDC |
|--------|---------------|--------------|
| **Latency** | 5-30 seconds | <100ms |
| **Database CPU** | High (continuous queries) | Minimal (WAL read) |
| **Throughput** | 500-1,000 events/sec | 100,000+ events/sec |
| **Scalability** | Single worker bottleneck | Horizontal (Kafka Connect cluster) |
| **Code complexity** | High (Python concurrency) | Zero (external service) |

### Why Debezium is faster

**Polling worker:**
```sql
-- Runs every 5 seconds (database load)
SELECT * FROM outbox_event_record 
WHERE published_at IS NULL 
ORDER BY created_at 
LIMIT 100 
FOR UPDATE SKIP LOCKED;
```

**Debezium CDC:**
- No queries to outbox table
- Reads PostgreSQL WAL only (separate from table I/O)
- Immediately triggers on COMMIT (no polling delay)
- Zero application code (external infrastructure)

---

## PostgreSQL WAL configuration

### Enable logical replication

```sql
-- Check current wal_level
SHOW wal_level;

-- If not 'logical', update postgresql.conf:
wal_level = logical
max_replication_slots = 4
max_wal_senders = 4
```

### Create replication slot (automatic via Debezium)

Debezium automatically creates:
- **Replication slot:** `debezium_outbox` (tracks WAL position)
- **Publication:** `debezium_publication` (defines which tables to capture)

**Manual verification:**
```sql
-- View replication slots
SELECT * FROM pg_replication_slots;

-- View publications
SELECT * FROM pg_publication;
SELECT * FROM pg_publication_tables;
```

---

## Troubleshooting

### Issue: Connector fails to start

**Symptoms:** Connector status shows `FAILED`.

**Common causes:**

1. **WAL level not logical:**
   ```sql
   -- Check and fix
   SHOW wal_level;  -- Must be 'logical'
   ALTER SYSTEM SET wal_level = 'logical';
   -- Restart PostgreSQL
   ```

2. **Missing table:**
   ```sql
   -- Verify outbox table exists
   SELECT * FROM information_schema.tables 
   WHERE table_name = 'outbox_event_record';
   ```

3. **Permission denied:**
   ```sql
   -- Grant replication permissions
   ALTER USER postgres WITH REPLICATION;
   ```

### Issue: Events not appearing in Kafka

**Diagnosis steps:**

1. **Check connector is running:**
   ```bash
   curl http://kafka-connect:8083/connectors/outbox-connector/status
   ```

2. **Check Kafka topics:**
   ```bash
   kafka-topics.sh --bootstrap-server kafka:9092 --list
   # Should see your event topics (e.g., user.created)
   ```

3. **Verify outbox table has events:**
   ```sql
   SELECT * FROM outbox_event_record ORDER BY created_at DESC LIMIT 10;
   ```

4. **Check Kafka Connect logs:**
   ```bash
   docker logs kafka-connect
   ```

### Issue: High database load

**Symptoms:** PostgreSQL CPU usage high after enabling CDC.

**Likely cause:** Too many `wal_sender` processes or aggressive polling.

**Solution:**
```sql
-- Tune WAL settings
ALTER SYSTEM SET max_wal_senders = 4;
ALTER SYSTEM SET wal_sender_timeout = '60s';
ALTER SYSTEM SET wal_keep_size = '512MB';
```

---

## See also

- {doc}`broker-selection-guide` - When to use Kafka vs RabbitMQ
- {doc}`transactional-outbox` - Outbox pattern implementation details
- {doc}`cross-service-communication` - Complete architecture with deployment examples
- [Debezium Documentation](https://debezium.io/documentation/)
- [PostgreSQL Logical Replication](https://www.postgresql.org/docs/current/logical-replication.html)

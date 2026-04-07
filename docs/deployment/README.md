# Deployment Documentation

Guide for running python-eventing with Kafka infrastructure.

## Quick start

[quickstart-docker-kafka.md](./quickstart-docker-kafka.md) - Complete setup with Docker Compose

## Two Publishing Patterns

python-eventing supports two approaches:

1. **Direct Publishing** - Publish events directly to Kafka (simpler, Kafka only)
2. **Transactional Outbox** - Write to DB, CDC publishes to Kafka (robust, requires PostgreSQL + Kafka Connect)

See quickstart for code examples and comparison table.

## Network modes

| Your app runs in | Kafka runs in | Bootstrap servers |
|------------------|---------------|------------------|
| Host machine | Docker | `localhost:9092` |
| Docker container | Docker | `kafka:9092` |
| Kubernetes/Cloud | Managed service | External URL |

## Files

- [quickstart-docker-kafka.md](./quickstart-docker-kafka.md) - Setup guide with examples
- [docker-compose.yml](../../docker-compose.yml) - Infrastructure (Kafka, PostgreSQL, CDC, UI)
- [.env.example](../../.env.example) - Configuration template

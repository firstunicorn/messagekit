# Eventing

Package-first universal event infrastructure for GridFlow microservices.

| Package | Transactional outbox | Kafka support | Typed cross-service contracts | Idempotent consumer patterns | Developer ergonomics |
| --- | --- | --- | --- | --- | --- |
| `python-eventing` | Yes | Yes | Yes | Yes | Facade, decorators, hooks |
| [`pyventus`](https://github.com/mdapena/pyventus) | No | No built-in Kafka data plane | General event abstractions | No built-in durable consumer pattern | Strong |
| [`fastapi-events`](https://github.com/melvinkcx/fastapi-events) | No | No Kafka data plane | Request-local event payloads | No | Strong inside FastAPI |

## Scope

- Transactional outbox primitives
- Event contracts and registry
- Kafka publishing and consumer base classes
- In-process emitter/subscriber facade and hooks

## Distribution

- PyPI distribution name: `python-eventing`
- Python import package: `eventing`

Services should consume the published package rather than a source checkout.
The package stays out of the synchronous request path; Kafka remains shared
infrastructure and each participating service uses local producer/consumer
clients.

## Local development

```powershell
poetry install
poetry build
poetry run pytest
```

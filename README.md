# Eventing

Package-first universal event infrastructure for microservices.

## Scope

- Transactional outbox primitives
- Event contracts and registry
- Kafka publishing and consumer base classes
- In-process emitter/subscriber facade and hooks

## Distribution

- PyPI distribution name: `python-eventing`
- Python import package: `eventing`

Services should consume the published package rather than a source checkout.
Kafka remains sharedinfrastructure and each participating service uses 
local producer/consumer clients.

## Local development

```powershell
poetry install
poetry build
poetry run pytest
```

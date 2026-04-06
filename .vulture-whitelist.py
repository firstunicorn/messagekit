# Vulture whitelist for intentionally unused code
# These are required by external interfaces (protocols/ABCs)

# IOutboxRepository interface from python-outbox-core
# get_unpublished() parameters are unused because Kafka Connect handles publishing,
# but they must exist for interface compliance with python-outbox-core.IOutboxRepository
SqlAlchemyOutboxRepository.get_unpublished.limit
SqlAlchemyOutboxRepository.get_unpublished.offset

"""Producer service simulation (uses EventBus + Outbox)."""

import logging
from pathlib import Path
import sys

# Add src to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)

from messaging.core.contracts.bus.event_bus import EventBus
from messaging.core.contracts import build_event_bus
from messaging.infrastructure.outbox import (
    SqlAlchemyOutboxRepository,
    OutboxEventHandler,
)
from messaging.infrastructure.persistence.orm_models.outbox_orm import OutboxEventRecord
from messaging.infrastructure.pubsub.kafka_publisher import KafkaEventPublisher
from faststream.confluent import KafkaBroker

from shared_events import TestEvent

logger = logging.getLogger(__name__)


class ProducerService:
    """Simulates producer microservice with EventBus + Outbox."""
    
    def __init__(self) -> None:
        self.engine: AsyncEngine | None = None
        self.session_factory: async_sessionmaker[AsyncSession] | None = None
        self.event_bus: EventBus | None = None
        self.kafka_broker: KafkaBroker | None = None
        self.kafka_publisher: KafkaEventPublisher | None = None
        
    async def start(self) -> None:
        """Start producer service."""
        # Database setup
        database_url = "postgresql+asyncpg://postgres:postgres@localhost:5432/eventing"
        self.engine = create_async_engine(database_url, echo=False)
        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # Create tables if needed
        from messaging.infrastructure.persistence.models import Base
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # Setup EventBus with outbox handler
        async with self.session_factory() as session:
            outbox_repo = SqlAlchemyOutboxRepository(session)
            outbox_handler = OutboxEventHandler(outbox_repo)
            
            self.event_bus = build_event_bus()
            self.event_bus.register(TestEvent, outbox_handler)
        
        # Setup Kafka for manual publishing
        self.kafka_broker = KafkaBroker("localhost:9092")
        await self.kafka_broker.connect()
        self.kafka_publisher = KafkaEventPublisher(self.kafka_broker)
        
        logger.info("Producer service initialized")
    
    async def emit_event(self, event: TestEvent) -> None:
        """Emit event via EventBus (writes to outbox)."""
        async with self.session_factory() as session:
            # Re-create outbox handler with new session
            outbox_repo = SqlAlchemyOutboxRepository(session)
            outbox_handler = OutboxEventHandler(outbox_repo)
            self.event_bus.handlers.clear()
            self.event_bus.register(TestEvent, outbox_handler)
            
            async with session.begin():
                await self.event_bus.emit(event)
            
            logger.info(f"Event emitted and persisted to outbox: {event.event_type}")
    
    async def get_outbox_count(self) -> int:
        """Get count of events in outbox."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(func.count()).select_from(OutboxEventRecord)
            )
            count = result.scalar() or 0
            return count
    
    async def publish_pending_events(self) -> None:
        """Manually publish pending events from outbox to Kafka.
        
        Simulates what Kafka Connect CDC would do in production.
        """
        async with self.session_factory() as session:
            # Get unpublished events
            result = await session.execute(
                select(OutboxEventRecord)
                .where(OutboxEventRecord.published_at == None)  # noqa: E711
            )
            events = result.scalars().all()
            
            logger.info(f"Publishing {len(events)} events from outbox...")
            
            for event_record in events:
                # Publish to Kafka
                await self.kafka_publisher.publish(event_record.payload)
                logger.info(f"Published event: {event_record.event_type} (id={event_record.id})")
    
    async def stop(self) -> None:
        """Stop producer service."""
        if self.kafka_broker:
            await self.kafka_broker.close()
        if self.engine:
            await self.engine.dispose()
        logger.info("Producer service stopped")

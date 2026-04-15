"""Consumer service simulation (subscribes to Kafka with idempotency)."""

import logging
from typing import Any
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
from faststream.confluent import KafkaBroker

from messaging.infrastructure.persistence.processed_message_store.processed_message_store import (
    SqlAlchemyProcessedMessageStore,
)
from messaging.infrastructure.persistence.orm_models.processed_message_orm import ProcessedMessage

logger = logging.getLogger(__name__)


class ConsumerService:
    """Simulates consumer microservice with Kafka subscription + idempotency."""
    
    def __init__(self) -> None:
        self.engine: AsyncEngine | None = None
        self.session_factory: async_sessionmaker[AsyncSession] | None = None
        self.kafka_broker: KafkaBroker | None = None
        self.received_events: list[dict[str, Any]] = []
        
    async def start(self) -> None:
        """Start consumer service."""
        # Database setup (consumer has own database in real scenario)
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
        
        # Setup Kafka consumer
        self.kafka_broker = KafkaBroker("localhost:9092")
        
        # Register subscriber handler
        @self.kafka_broker.subscriber("test.event_emitted")
        async def handle_test_event(message: dict[str, Any]) -> None:
            """Handle incoming test event with idempotency."""
            logger.info(f"Received event: {message.get('eventType', 'unknown')}")
            
            # Extract message ID for idempotency check
            message_id = message.get("id") or message.get("messageId")
            if not message_id:
                logger.warning("Message has no ID, skipping idempotency check")
                self.received_events.append(message)
                return
            
            # Idempotency check
            async with self.session_factory() as session:
                store = SqlAlchemyProcessedMessageStore(session)
                
                async with session.begin():
                    # Check if already processed
                    was_processed = await store.was_processed(message_id)
                    
                    if was_processed:
                        logger.info(f"Message {message_id} already processed (idempotent skip)")
                        return
                    
                    # Process business logic (just store in memory for E2E test)
                    self.received_events.append(message)
                    logger.info(f"Processing event: user_id={message.get('data', {}).get('user_id')}")
                    
                    # Mark as processed
                    await store.mark_processed(
                        message_id=message_id,
                        event_type=message.get("eventType", "unknown"),
                        payload=message
                    )
                    logger.info(f"Message {message_id} marked as processed")
        
        # Start broker
        await self.kafka_broker.start()
        logger.info("Consumer service initialized and subscribed to test.event_emitted")
    
    def get_received_events(self) -> list[dict[str, Any]]:
        """Get list of received events."""
        return self.received_events
    
    async def get_processed_count(self) -> int:
        """Get count of processed messages in database."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(func.count()).select_from(ProcessedMessage)
            )
            count = result.scalar() or 0
            return count
    
    async def stop(self) -> None:
        """Stop consumer service."""
        if self.kafka_broker:
            await self.kafka_broker.close()
        if self.engine:
            await self.engine.dispose()
        logger.info("Consumer service stopped")

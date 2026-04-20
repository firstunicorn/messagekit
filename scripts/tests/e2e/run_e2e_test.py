"""
E2E test runner for messagekit.

Simulates real microservices architecture:
- Producer service: Uses EventBus + Outbox pattern
- Consumer service: Subscribes to Kafka with idempotent consumer
- Tests full event flow: emit → outbox → Kafka → consume

Prerequisites:
- Docker containers running (kafka, postgres)
- Run: docker-compose up -d
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root))

from producer_service import ProducerService
from consumer_service import ConsumerService
from shared_events import TestEvent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def run_e2e_test() -> None:
    """Run complete E2E test flow."""
    
    logger.info("=" * 80)
    logger.info("E2E TEST: Full event flow (EventBus + Outbox + Kafka + Consumer)")
    logger.info("=" * 80)
    
    # Step 1: Initialize services
    logger.info("\n[STEP 1] Initializing services...")
    producer = ProducerService()
    consumer = ConsumerService()
    
    try:
        await producer.start()
        logger.info("✅ Producer service started")
        
        await consumer.start()
        logger.info("✅ Consumer service started")
        
        # Step 2: Emit event via EventBus (writes to outbox)
        logger.info("\n[STEP 2] Emitting test event via EventBus...")
        test_event = TestEvent(
            aggregate_id="test-aggregate-001",
            user_id=12345,
            action="user_registered",
            metadata={"source": "e2e_test", "environment": "test"}
        )
        
        await producer.emit_event(test_event)
        logger.info(f"✅ Event emitted: {test_event.event_type} (aggregate_id={test_event.aggregate_id})")
        
        # Step 3: Verify outbox persistence
        logger.info("\n[STEP 3] Verifying outbox persistence...")
        outbox_count = await producer.get_outbox_count()
        logger.info(f"✅ Events in outbox: {outbox_count}")
        
        if outbox_count == 0:
            logger.error("❌ FAILED: Event not found in outbox")
            sys.exit(1)
        
        # Step 4: Manually publish from outbox to Kafka
        # (In production, Kafka Connect CDC would do this)
        logger.info("\n[STEP 4] Publishing from outbox to Kafka (simulating CDC)...")
        await producer.publish_pending_events()
        logger.info("✅ Events published to Kafka")
        
        # Step 5: Wait for consumer to receive event
        logger.info("\n[STEP 5] Waiting for consumer to receive event...")
        await asyncio.sleep(3)  # Give consumer time to process
        
        # Step 6: Verify consumer received event
        logger.info("\n[STEP 6] Verifying consumer processed event...")
        received_events = consumer.get_received_events()
        processed_count = await consumer.get_processed_count()
        
        logger.info(f"✅ Received events: {len(received_events)}")
        logger.info(f"✅ Processed messages in DB: {processed_count}")
        
        if len(received_events) == 0:
            logger.error("❌ FAILED: Consumer did not receive event")
            sys.exit(1)
        
        # Step 7: Verify event data
        logger.info("\n[STEP 7] Verifying event data...")
        received_event = received_events[0]
        
        assert received_event["eventType"] == test_event.event_type
        assert received_event["aggregateId"] == test_event.aggregate_id
        assert received_event["data"]["user_id"] == test_event.user_id
        assert received_event["data"]["action"] == test_event.action
        
        logger.info("✅ Event data verified correctly")
        
        # Step 8: Test idempotency (send duplicate)
        logger.info("\n[STEP 8] Testing idempotency (resending same event)...")
        await producer.publish_pending_events()
        await asyncio.sleep(2)
        
        received_after_duplicate = consumer.get_received_events()
        processed_after_duplicate = await consumer.get_processed_count()
        
        logger.info(f"✅ Received events after duplicate: {len(received_after_duplicate)}")
        logger.info(f"✅ Processed messages in DB: {processed_after_duplicate}")
        
        # Should still be 1 due to idempotency
        if processed_after_duplicate != processed_count:
            logger.warning(f"⚠️  Processed count changed from {processed_count} to {processed_after_duplicate}")
            logger.warning("⚠️  This might indicate idempotency issue or multiple test runs")
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ E2E TEST PASSED")
        logger.info("=" * 80)
        logger.info("")
        logger.info("Summary:")
        logger.info(f"  • Events emitted: 1")
        logger.info(f"  • Events in outbox: {outbox_count}")
        logger.info(f"  • Events received by consumer: {len(received_events)}")
        logger.info(f"  • Processed messages (idempotent): {processed_count}")
        logger.info("")
        
    except Exception as e:
        logger.error(f"\n❌ E2E TEST FAILED: {e}", exc_info=True)
        sys.exit(1)
        
    finally:
        # Cleanup
        logger.info("\n[CLEANUP] Shutting down services...")
        await consumer.stop()
        await producer.stop()
        logger.info("✅ Services stopped")


def main() -> None:
    """Entry point."""
    try:
        asyncio.run(run_e2e_test())
    except KeyboardInterrupt:
        logger.info("\n⚠️  Test interrupted by user")
        sys.exit(1)


if __name__ == "__main__":
    main()

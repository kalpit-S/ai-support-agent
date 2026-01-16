import time
import logging
from typing import List, Callable
from dataclasses import dataclass

import redis

from config import settings


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class Batch:
    """Represents a batch of messages ready for processing."""
    customer_id: int
    batch_id: str
    message_ids: List[int]
    last_updated: float


class Batcher:
    """Polls Redis for message batches and processes them."""

    def __init__(
        self,
        redis_client: redis.Redis,
        batch_window_seconds: int = 5,
        poll_interval_seconds: float = 1.0,
    ):
        self.redis = redis_client
        self.batch_window = batch_window_seconds
        self.poll_interval = poll_interval_seconds

    def find_ready_batches(self) -> List[Batch]:
        """Find batches that have been idle for longer than the batch window."""
        ready_batches = []
        now = time.time()

        # Scan Redis for all batch:customer:*:updated keys
        cursor = 0
        while True:
            cursor, keys = self.redis.scan(cursor, match="batch:customer:*:updated")

            for updated_key in keys:
                # Parse the customer ID from the key
                parts = updated_key.split(":")
                if len(parts) != 4 or parts[1] != "customer":
                    continue
                try:
                    customer_id = int(parts[2])
                except ValueError:
                    logger.warning(f"Invalid customer_id in key: {updated_key}")
                    continue

                # Check if batch has been idle long enough
                updated_str = self.redis.get(updated_key)
                if not updated_str:
                    continue

                try:
                    last_updated = float(updated_str)
                except ValueError:
                    logger.warning(f"Invalid timestamp for {updated_key}: {updated_str}")
                    continue

                idle_time = now - last_updated
                if idle_time < self.batch_window:
                    continue

                # Get batch data
                batch_key = f"batch:customer:{customer_id}"
                batch_id = self.redis.get(f"{batch_key}:id")
                message_ids_str = self.redis.lrange(batch_key, 0, -1)

                if not batch_id or not message_ids_str:
                    logger.warning(f"Incomplete batch data for customer {customer_id}")
                    continue

                try:
                    message_ids = [int(mid) for mid in message_ids_str]
                except ValueError:
                    logger.warning(f"Invalid message IDs for customer {customer_id}: {message_ids_str}")
                    continue

                ready_batches.append(Batch(
                    customer_id=customer_id,
                    batch_id=batch_id,
                    message_ids=message_ids,
                    last_updated=last_updated,
                ))

            if cursor == 0:
                break

        return ready_batches

    def cleanup_batch(self, batch: Batch) -> None:
        """Remove a processed batch from Redis."""
        batch_key = f"batch:customer:{batch.customer_id}"
        self.redis.delete(batch_key, f"{batch_key}:id", f"{batch_key}:updated")
        logger.info(f"Cleaned up batch {batch.batch_id} for customer {batch.customer_id}")

    def run(self, process_callback: Callable[[Batch], None]) -> None:
        """Main loop: poll for batches and process them."""
        logger.info(f"Batcher starting. Window: {self.batch_window}s, Poll: {self.poll_interval}s")

        while True:
            try:
                ready_batches = self.find_ready_batches()

                if ready_batches:
                    logger.info(f"Found {len(ready_batches)} ready batch(es)")

                for batch in ready_batches:
                    logger.info(
                        f"Processing batch {batch.batch_id} "
                        f"for customer {batch.customer_id} "
                        f"with {len(batch.message_ids)} message(s)"
                    )

                    try:
                        process_callback(batch)
                        self.cleanup_batch(batch)
                    except Exception as e:
                        logger.error(f"Error processing batch {batch.batch_id}: {e}")

                time.sleep(self.poll_interval)

            except redis.ConnectionError as e:
                logger.error(f"Redis connection error: {e}. Retrying in 5s...")
                time.sleep(5)
            except Exception as e:
                logger.error(f"Unexpected error in batcher loop: {e}")
                time.sleep(5)


def create_batcher() -> Batcher:
    """Create a Batcher with settings from config."""
    redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    return Batcher(
        redis_client=redis_client,
        batch_window_seconds=settings.batch_window_seconds,
        poll_interval_seconds=settings.poll_interval_seconds,
    )

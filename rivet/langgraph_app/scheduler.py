"""
Scheduler Process - Enqueues ingestion jobs periodically

Runs continuously, adding source URLs to Redis queue for worker processing.
"""

import time
import logging
import redis
from langgraph_app.config import settings

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_scheduler():
    """
    Main scheduler loop

    Continuously:
    1. Query for new source URLs (from database or config)
    2. Enqueue to Redis
    3. Sleep for interval
    4. Repeat
    """
    logger.info("Scheduler starting...")
    logger.info(f"Redis URL: {settings.REDIS_URL}")

    # Connect to Redis
    try:
        r = redis.Redis.from_url(settings.REDIS_URL)
        r.ping()
        logger.info("Redis connection established")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        return

    # TODO: Load sources from database or config file
    # For now, use hardcoded list
    sources = [
        # Example industrial documentation URLs
        "https://literature.rockwellautomation.com/idc/groups/literature/documents/um/1756-um001_-en-p.pdf",
        "https://cache.industry.siemens.com/dl/files/465/36932465/att_106119/v1/s71200_system_manual_en-US_en-US.pdf",
    ]

    logger.info(f"Loaded {len(sources)} source URLs")
    logger.info("Scheduler ready")

    # Main loop
    run_count = 0

    while True:
        try:
            run_count += 1
            logger.info(f"Scheduler run #{run_count}")

            # Enqueue each source
            for url in sources:
                try:
                    # Check if already in queue
                    queue_length = r.llen("kb_ingest_jobs")

                    if queue_length > 100:
                        logger.warning(f"Queue full ({queue_length} jobs), skipping enqueue")
                        break

                    # Add to queue
                    r.rpush("kb_ingest_jobs", url)
                    logger.info(f"Enqueued: {url}")

                except Exception as e:
                    logger.error(f"Failed to enqueue {url}: {e}")

            # Sleep for 1 hour (3600 seconds)
            logger.info("Sleeping for 1 hour...")
            time.sleep(3600)

        except KeyboardInterrupt:
            logger.info("Scheduler shutting down (keyboard interrupt)")
            break

        except Exception as e:
            logger.error(f"Scheduler error: {e}", exc_info=True)
            time.sleep(60)  # Back off before retrying


if __name__ == "__main__":
    run_scheduler()

"""
Scheduler process - Periodically enqueues source URLs for ingestion
"""

import logging
import redis
import time
from langgraph_app.config import settings

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

logger = logging.getLogger(__name__)


def run_scheduler():
    """
    Main scheduler loop - enqueues source URLs into Redis
    """
    logger.info("Starting Rivet scheduler...")
    logger.info(f"Redis URL: {settings.REDIS_URL}")
    logger.info(f"Scheduler interval: {settings.SCHEDULER_INTERVAL}s")

    # Connect to Redis
    r = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

    # TODO: In production, query Postgres sources table
    # For V1, use hardcoded test URLs
    source_urls = [
        "https://example.com/manual1.pdf",
        "https://example.com/manual2.pdf",
    ]

    logger.info(f"Scheduler ready. Will enqueue {len(source_urls)} URLs every {settings.SCHEDULER_INTERVAL}s")

    iteration = 0
    while True:
        try:
            iteration += 1
            logger.info(f"Scheduler iteration {iteration}")

            # Enqueue source URLs
            for url in source_urls:
                r.rpush("kb_ingest_jobs", url)
                logger.info(f"Enqueued: {url}")

            logger.info(f"Enqueued {len(source_urls)} jobs. Sleeping for {settings.SCHEDULER_INTERVAL}s")

            # Sleep until next iteration
            time.sleep(settings.SCHEDULER_INTERVAL)

        except Exception as e:
            logger.error(f"Scheduler error: {e}", exc_info=True)
            time.sleep(60)  # Back off on error


if __name__ == "__main__":
    run_scheduler()

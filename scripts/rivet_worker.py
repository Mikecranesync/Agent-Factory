#!/usr/bin/env python3
"""
24/7 Background Worker - KB Ingestion Pipeline

Polls Redis queue 'kb_ingest_jobs' every 30 seconds.
Runs ingestion_chain for each URL.
Sends Telegram notifications in VERBOSE mode.

Usage:
    poetry run python scripts/rivet_worker.py

Systemd service: deploy/vps/rivet-worker.service
"""

import os
import sys
import time
import signal
import logging
import redis
from pathlib import Path
from dotenv import load_dotenv

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_factory.workflows.ingestion_chain import ingest_source
from agent_factory.observability.ingestion_monitor import IngestionMonitor
from agent_factory.observability.telegram_notifier import TelegramNotifier
from agent_factory.core.database_manager import DatabaseManager

# Logging setup
log_dir = Path("data/logs")
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "rivet_worker.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Shutdown flag
shutdown_requested = False

def signal_handler(signum, frame):
    """Handle SIGTERM/SIGINT for graceful shutdown."""
    global shutdown_requested
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    shutdown_requested = True

# Register signal handlers
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

def main():
    """Main worker loop."""
    logger.info("=" * 80)
    logger.info("RIVET WORKER - 24/7 KB INGESTION DAEMON")
    logger.info("=" * 80)

    # Load environment
    load_dotenv()

    # Connect to Redis
    redis_host = os.getenv("VPS_KB_HOST", "localhost")
    redis_port = int(os.getenv("VPS_KB_PORT", "6379"))

    logger.info(f"Connecting to Redis: {redis_host}:{redis_port}")

    try:
        redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            decode_responses=True,
            socket_connect_timeout=10,
            socket_timeout=60  # Increased for blpop operations
        )
        # Test connection
        redis_client.ping()
        logger.info("Redis connection established")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        return 1

    # Initialize observability
    try:
        db = DatabaseManager()

        # Get notification mode from environment (default: VERBOSE)
        notification_mode = os.getenv("KB_NOTIFICATION_MODE", "VERBOSE")

        notifier = TelegramNotifier(
            bot_token=os.getenv("ORCHESTRATOR_BOT_TOKEN"),
            chat_id=int(os.getenv("TELEGRAM_ADMIN_CHAT_ID", "8445149012")),
            mode=notification_mode,
            quiet_hours_start=int(os.getenv("NOTIFICATION_QUIET_START", "23")),
            quiet_hours_end=int(os.getenv("NOTIFICATION_QUIET_END", "7")),
            db_manager=db
        )

        monitor = IngestionMonitor(db, telegram_notifier=notifier)

        logger.info(f"Observability initialized (mode={notification_mode})")
    except Exception as e:
        logger.error(f"Observability initialization failed: {e}")
        logger.warning("Continuing without monitoring...")
        monitor = None

    # Main polling loop
    poll_interval = 5  # seconds (for blpop timeout)
    idle_count = 0
    processed_count = 0

    logger.info("Starting polling loop (Ctrl+C to stop)")

    while not shutdown_requested:
        try:
            # Pop URL from Redis queue (blocking pop with timeout)
            result = redis_client.blpop("kb_ingest_jobs", timeout=poll_interval)

            if result:
                queue_name, url = result
                idle_count = 0
                processed_count += 1

                logger.info("")
                logger.info("=" * 80)
                logger.info(f"[{processed_count}] Processing URL from queue: {url}")
                logger.info("=" * 80)

                # Run ingestion (ingestion_chain internally uses monitor)
                start_time = time.time()

                try:
                    ingest_result = ingest_source(url)

                    duration = time.time() - start_time

                    if ingest_result.get("success"):
                        atoms_created = ingest_result.get('atoms_created', 0)
                        logger.info(
                            f"[SUCCESS] {url}\n"
                            f"  Atoms created: {atoms_created}\n"
                            f"  Duration: {duration:.1f}s"
                        )
                    else:
                        errors = ingest_result.get('errors', [])
                        logger.error(
                            f"[FAILED] {url}\n"
                            f"  Errors: {errors}\n"
                            f"  Duration: {duration:.1f}s"
                        )

                except Exception as e:
                    logger.error(f"[EXCEPTION] Ingestion failed: {e}", exc_info=True)

            else:
                # Queue empty
                idle_count += 1
                if idle_count % 20 == 0:  # Log every ~100 seconds when idle
                    logger.info(
                        f"Queue empty (checked {idle_count} times, "
                        f"processed {processed_count} total URLs)"
                    )

        except redis.ConnectionError as e:
            logger.error(f"Redis connection error: {e}")
            logger.info("Waiting 60s before retry...")
            time.sleep(60)  # Wait 1 minute before retry

        except Exception as e:
            logger.error(f"Worker error: {e}", exc_info=True)
            logger.info("Waiting 10s before retry...")
            time.sleep(10)  # Backoff on error

    # Graceful shutdown
    logger.info("")
    logger.info("=" * 80)
    logger.info("WORKER SHUTDOWN COMPLETE")
    logger.info(f"Total URLs processed: {processed_count}")
    logger.info("=" * 80)

    # Shutdown monitor
    if monitor:
        import asyncio
        try:
            asyncio.run(monitor.shutdown())
        except Exception as e:
            logger.error(f"Monitor shutdown failed: {e}")

    return 0

if __name__ == "__main__":
    sys.exit(main())

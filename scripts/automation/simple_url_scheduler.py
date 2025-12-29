#!/usr/bin/env python3
"""
Simple URL Scheduler - Pushes kb_seed_urls.py to Redis Queue

Reads curated URLs from kb_seed_urls.py and pushes them to VPS Redis queue.
The 24/7 worker (rivet_worker.py) then processes them automatically.

Usage:
    poetry run python scripts/automation/simple_url_scheduler.py

Systemd service: deploy/vps/rivet-scheduler.service
"""

import os
import sys
import redis
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import from kb_seed_urls.py (in scripts/ directory)
import importlib.util
spec = importlib.util.spec_from_file_location("kb_seed_urls", project_root / "scripts" / "kb_seed_urls.py")
kb_seed_urls = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kb_seed_urls)

SEED_URLS = kb_seed_urls.SEED_URLS
URL_METADATA = kb_seed_urls.URL_METADATA

# Logging setup
log_dir = Path("data/logs")
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "simple_url_scheduler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def send_telegram_notification(message: str):
    """Send notification via Telegram"""
    bot_token = os.getenv("ORCHESTRATOR_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_ADMIN_CHAT_ID", "8445149012")

    if not bot_token:
        logger.warning("ORCHESTRATOR_BOT_TOKEN not found, skipping notification")
        return

    try:
        import requests
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        response = requests.post(url, json=data, timeout=10)
        if response.status_code == 200:
            logger.info("Telegram notification sent")
        else:
            logger.error(f"Telegram failed: {response.text}")
    except Exception as e:
        logger.error(f"Failed to send Telegram: {e}")


def main():
    """Push all kb_seed_urls.py URLs to Redis queue"""
    start_time = datetime.now()

    logger.info("=" * 80)
    logger.info("SIMPLE URL SCHEDULER - STARTING")
    logger.info("=" * 80)
    logger.info(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

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
            socket_connect_timeout=5,
            socket_timeout=5
        )
        redis_client.ping()
        logger.info("Redis connection established")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        send_telegram_notification(f"❌ URL Scheduler FAILED\n\nRedis connection error: {str(e)}")
        return 1

    # Check queue length before
    queue_before = redis_client.llen("kb_ingest_jobs")
    logger.info(f"Queue length before: {queue_before}")

    # Push URLs to queue
    logger.info(f"\nPushing {len(SEED_URLS)} URLs to queue...")

    pushed_count = 0
    for url in SEED_URLS:
        try:
            redis_client.rpush("kb_ingest_jobs", url)
            pushed_count += 1
            if pushed_count % 5 == 0:
                logger.info(f"  Pushed {pushed_count}/{len(SEED_URLS)} URLs...")
        except Exception as e:
            logger.error(f"Failed to push {url}: {e}")

    # Check queue length after
    queue_after = redis_client.llen("kb_ingest_jobs")
    logger.info(f"\nQueue length after: {queue_after}")
    logger.info(f"Successfully pushed {pushed_count} URLs")

    # Generate summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    summary = f"""
📋 **URL Scheduler Report**
🕐 **Time:** {start_time.strftime('%Y-%m-%d %H:%M')}

**URLs Pushed:**
"""

    for manufacturer, count in URL_METADATA.items():
        if manufacturer != "total":
            summary += f"- {manufacturer.replace('_', ' ').title()}: {count}\n"

    summary += f"\n**Total:** {pushed_count} URLs\n"
    summary += f"**Queue:** {queue_before} → {queue_after}\n"
    summary += f"**Duration:** {duration:.1f}s\n"
    summary += f"\n✅ Worker will process these automatically"

    logger.info(summary)
    send_telegram_notification(summary)

    logger.info("=" * 80)
    logger.info("SIMPLE URL SCHEDULER - COMPLETE")
    logger.info("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())

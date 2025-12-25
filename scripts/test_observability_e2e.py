#!/usr/bin/env python3
"""
End-to-end test for KB Observability Platform.

Tests the complete integration:
1. IngestionMonitor tracks 7-stage pipeline
2. TelegramNotifier queues batch summaries
3. Database writes metrics
4. Telegram sends notification after 5 minutes

Usage:
    poetry run python scripts/test_observability_e2e.py
"""

import os
import sys
import time
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def main():
    """Run end-to-end observability test."""
    print("=" * 60)
    print("KB Observability End-to-End Test")
    print("=" * 60)
    print()
    print("Configuration:")
    print(f"  Mode: {os.getenv('KB_NOTIFICATION_MODE', 'BATCH')}")
    print(f"  Bot: @RivetCeo_bot")
    print(f"  Chat ID: {os.getenv('TELEGRAM_ADMIN_CHAT_ID', '8445149012')}")
    print(f"  Bot Token: {os.getenv('ORCHESTRATOR_BOT_TOKEN', 'NOT SET')[:20]}...")
    print()

    # Test URL (public Rockwell PDF)
    test_url = "https://literature.rockwellautomation.com/idc/groups/literature/documents/um/1756-um001_-en-p.pdf"

    print(f"Ingesting test source:")
    print(f"  {test_url}")
    print()
    print("This will:")
    print("  1. Download and parse the PDF (Stage 1-2)")
    print("  2. Generate knowledge atoms with LLM (Stage 3-5)")
    print("  3. Create embeddings and store to database (Stage 6-7)")
    print("  4. Queue metrics for database write")
    print("  5. Queue notification for next batch summary (5 min)")
    print()

    # Import after environment is loaded
    from agent_factory.workflows.ingestion_chain import ingest_source

    print("Starting ingestion...")
    print()

    start_time = time.time()

    try:
        result = ingest_source(test_url)

        duration = time.time() - start_time

        print()
        print("=" * 60)
        print("INGESTION RESULTS")
        print("=" * 60)

        if result.get("success"):
            print("Status: [OK] SUCCESS")
            print()
            print(f"Atoms created: {result.get('atoms_created', 0)}")
            print(f"Atoms failed: {result.get('atoms_failed', 0)}")
            print(f"Duration: {duration:.1f} seconds")
            print(f"Errors: {len(result.get('errors', []))}")

            if result.get('errors'):
                print()
                print("Errors encountered:")
                for error in result.get('errors', []):
                    print(f"  - {error}")

            print()
            print("=" * 60)
            print("OBSERVABILITY STATUS")
            print("=" * 60)
            print("[DB] Metrics queued for database write")
            print("[TG] Notification queued for next batch summary (5 min)")
            print()
            print("Waiting 30 seconds for background writer flush...")

            time.sleep(30)

            print()
            print("=" * 60)
            print("TEST COMPLETE")
            print("=" * 60)
            print()
            print("Next steps:")
            print()
            print("  1. Wait 5 minutes for batch summary notification")
            print("     - Open Telegram and check @RivetCeo_bot")
            print("     - You should receive a batch summary message")
            print()
            print("  2. Check Telegram @RivetCeo_bot for message:")
            print("     Expected format:")
            print("     ```")
            print("     [SUMMARY] KB Ingestion Summary (Last 5 min)")
            print("     ")
            print("     Sources: 1 processed")
            print("     [OK] Success: 1 (100%)")
            print("     ")
            print("     Atoms: X created, 0 failed")
            print("     Avg Duration: X,XXXms")
            print("     Avg Quality: XX%")
            print("     ")
            print("     #kb_summary #batch")
            print("     ```")
            print()
            print("  3. Verify database has metrics (VPS):")
            print("     ```")
            print("     ssh vps")
            print("     psql -U rivet -d rivet")
            print("     SELECT source_url, atoms_created, total_duration_ms, status")
            print("     FROM ingestion_metrics_realtime")
            print("     ORDER BY created_at DESC")
            print("     LIMIT 5;")
            print("     ```")
            print()
            print("=" * 60)

        else:
            print("Status: [FAIL] FAILED")
            print()
            print(f"Duration: {duration:.1f} seconds")
            print(f"Errors: {len(result.get('errors', []))}")
            print()
            print("Error details:")
            for error in result.get('errors', []):
                print(f"  - {error}")

    except Exception as e:
        print()
        print("=" * 60)
        print("TEST FAILED")
        print("=" * 60)
        print(f"Error: {e}")
        print()
        print("Troubleshooting:")
        print("  1. Check .env has required variables:")
        print("     - ORCHESTRATOR_BOT_TOKEN")
        print("     - TELEGRAM_ADMIN_CHAT_ID=8445149012")
        print("     - KB_NOTIFICATION_MODE=BATCH")
        print()
        print("  2. Check bot is responding:")
        print("     poetry run python test_telegram_live.py")
        print()
        print("  3. Check database connection:")
        print("     poetry run python -c \"from agent_factory.core.database_manager import DatabaseManager; db = DatabaseManager(); print(db.health_check_all())\"")
        print()
        raise


if __name__ == "__main__":
    main()

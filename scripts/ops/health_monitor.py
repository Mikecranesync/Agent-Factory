"""
Memory System Health Monitor

Monitors all database providers and reports status.
Can be run as a cron job for continuous monitoring.

Run:
    poetry run python scripts/ops/health_monitor.py

Options:
    --alert           Send alerts on failures (Telegram)
    --json            Output JSON format
    --continuous      Run continuously (check every 5 minutes)
    --once            Run once and exit (default)
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def check_provider_health(db_manager):
    """
    Check health of all providers.

    Returns:
        dict: {provider_name: {healthy: bool, latency_ms: float, error: str}}
    """
    health_status = {}

    for provider_name in db_manager.providers:
        provider = db_manager.providers[provider_name]

        start_time = time.time()
        try:
            is_healthy = provider.health_check()
            latency_ms = (time.time() - start_time) * 1000

            health_status[provider_name] = {
                "healthy": is_healthy,
                "latency_ms": round(latency_ms, 2),
                "error": None if is_healthy else "Health check failed",
                "checked_at": datetime.now().isoformat()
            }

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000

            health_status[provider_name] = {
                "healthy": False,
                "latency_ms": round(latency_ms, 2),
                "error": str(e),
                "checked_at": datetime.now().isoformat()
            }

    return health_status


def check_query_performance(db_manager):
    """
    Check query performance by running a simple test query.

    Returns:
        dict: {success: bool, latency_ms: float, error: str}
    """
    start_time = time.time()

    try:
        # Simple query to test performance
        result = db_manager.execute_query("SELECT 1", fetch_mode="one")

        latency_ms = (time.time() - start_time) * 1000

        return {
            "success": True,
            "latency_ms": round(latency_ms, 2),
            "error": None,
            "tested_at": datetime.now().isoformat()
        }

    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000

        return {
            "success": False,
            "latency_ms": round(latency_ms, 2),
            "error": str(e),
            "tested_at": datetime.now().isoformat()
        }


def check_table_counts(db_manager):
    """
    Check row counts for key tables.

    Returns:
        dict: {table_name: row_count}
    """
    tables = [
        "session_memories",
        "knowledge_atoms",
        "settings",
    ]

    counts = {}

    for table in tables:
        try:
            result = db_manager.execute_query(
                f"SELECT COUNT(*) FROM {table}",
                fetch_mode="one"
            )

            counts[table] = result[0] if result else 0

        except Exception as e:
            # Table may not exist
            counts[table] = None

    return counts


def send_telegram_alert(message: str):
    """
    Send alert via Telegram.

    Args:
        message: Alert message to send
    """
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    admin_chat_id = os.getenv("TELEGRAM_ADMIN_CHAT_ID")

    if not bot_token or not admin_chat_id:
        print("[WARN] Telegram credentials not configured - alert not sent")
        return

    try:
        import requests

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": admin_chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }

        response = requests.post(url, json=payload, timeout=10)

        if response.status_code == 200:
            print("[OK] Telegram alert sent")
        else:
            print(f"[ERROR] Telegram alert failed: {response.status_code}")

    except Exception as e:
        print(f"[ERROR] Failed to send Telegram alert: {e}")


def generate_alert_message(health_status, query_perf, table_counts):
    """
    Generate alert message for failures.

    Args:
        health_status: Provider health status
        query_perf: Query performance results
        table_counts: Table row counts

    Returns:
        str: Alert message or None if no issues
    """
    issues = []

    # Check provider health
    healthy_count = sum(1 for status in health_status.values() if status["healthy"])
    total_count = len(health_status)

    if healthy_count == 0:
        issues.append("🚨 CRITICAL: All database providers are DOWN")
    elif healthy_count < total_count:
        down_providers = [name for name, status in health_status.items() if not status["healthy"]]
        issues.append(f"⚠️ WARNING: Providers down: {', '.join(down_providers)}")

    # Check query performance
    if not query_perf["success"]:
        issues.append(f"❌ Query test failed: {query_perf['error']}")
    elif query_perf["latency_ms"] > 1000:
        issues.append(f"⏱️ Slow query detected: {query_perf['latency_ms']:.0f}ms")

    # Check table counts (if any are None, table doesn't exist)
    missing_tables = [table for table, count in table_counts.items() if count is None]
    if missing_tables:
        issues.append(f"📋 Missing tables: {', '.join(missing_tables)}")

    if not issues:
        return None

    # Generate alert message
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    message = f"**Memory System Alert**\n{timestamp}\n\n"
    message += "\n".join(issues)

    message += "\n\n**Provider Status:**\n"
    for name, status in health_status.items():
        icon = "✅" if status["healthy"] else "❌"
        latency = f"{status['latency_ms']:.0f}ms" if status["healthy"] else "N/A"
        message += f"{icon} {name}: {latency}\n"

    return message


def print_health_status(health_status, query_perf, table_counts, output_json=False):
    """
    Print health status to console.

    Args:
        health_status: Provider health status
        query_perf: Query performance results
        table_counts: Table row counts
        output_json: If True, output JSON format
    """
    if output_json:
        output = {
            "timestamp": datetime.now().isoformat(),
            "providers": health_status,
            "query_performance": query_perf,
            "table_counts": table_counts
        }
        print(json.dumps(output, indent=2))
        return

    # ASCII output
    print("\n" + "="*60)
    print(f"MEMORY SYSTEM HEALTH CHECK - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    # Provider health
    print("\n[PROVIDERS]")
    for name, status in health_status.items():
        icon = "[OK]" if status["healthy"] else "[DOWN]"
        latency = f"{status['latency_ms']:.0f}ms" if status["healthy"] else "N/A"
        print(f"{icon} {name:15s} | Latency: {latency:8s}")
        if status["error"]:
            print(f"      Error: {status['error']}")

    # Query performance
    print("\n[QUERY PERFORMANCE]")
    if query_perf["success"]:
        print(f"[OK] Test query: {query_perf['latency_ms']:.0f}ms")
    else:
        print(f"[FAIL] Test query failed: {query_perf['error']}")

    # Table counts
    print("\n[TABLE COUNTS]")
    for table, count in table_counts.items():
        if count is not None:
            print(f"  {table:20s}: {count:8,d} rows")
        else:
            print(f"  {table:20s}: [TABLE NOT FOUND]")

    # Summary
    healthy_count = sum(1 for status in health_status.values() if status["healthy"])
    total_count = len(health_status)

    print("\n" + "-"*60)
    if healthy_count == total_count:
        print(f"[OK] All {total_count} providers healthy")
    elif healthy_count > 0:
        print(f"[WARNING] {healthy_count}/{total_count} providers healthy")
    else:
        print(f"[CRITICAL] All providers down")

    print("="*60 + "\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Memory system health monitor")
    parser.add_argument("--alert", action="store_true", help="Send alerts on failures")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    parser.add_argument("--continuous", action="store_true", help="Run continuously (check every 5 minutes)")
    parser.add_argument("--once", action="store_true", help="Run once and exit (default)")

    args = parser.parse_args()

    # Initialize DatabaseManager
    try:
        from agent_factory.core.database_manager import DatabaseManager

        db = DatabaseManager()

    except Exception as e:
        print(f"[ERROR] Failed to initialize DatabaseManager: {e}")
        sys.exit(1)

    # Main monitoring loop
    while True:
        # Check health
        health_status = check_provider_health(db)
        query_perf = check_query_performance(db)
        table_counts = check_table_counts(db)

        # Print status
        print_health_status(health_status, query_perf, table_counts, output_json=args.json)

        # Send alerts if enabled
        if args.alert:
            alert_message = generate_alert_message(health_status, query_perf, table_counts)
            if alert_message:
                send_telegram_alert(alert_message)

        # Exit if running once
        if args.once or not args.continuous:
            break

        # Sleep for 5 minutes before next check
        print("[INFO] Sleeping for 5 minutes...")
        time.sleep(300)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Send test messages to RIVET CEO Bot via Telegram API.

Usage:
    python scripts/test_bot.py
    python scripts/test_bot.py --custom "What is a motor starter?"
"""
import argparse
import os
import time
from datetime import datetime

import requests
from dotenv import load_dotenv

# Load environment
load_dotenv()

BOT_TOKEN = os.getenv("ORCHESTRATOR_BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("TELEGRAM_ADMIN_CHAT_ID", "8445149012")

# Predefined test queries
TEST_QUERIES = [
    "How do I fix F0003 fault on Siemens G120?",
    "What is a PLC?",
    "Troubleshoot Allen Bradley PowerFlex 525"
]


def send_test_message(text: str, delay: float = 2.0) -> dict:
    """
    Send message to bot via Telegram API.

    Args:
        text: Message text to send
        delay: Delay in seconds before sending (to avoid rate limits)

    Returns:
        API response dict
    """
    if not BOT_TOKEN:
        raise ValueError("ORCHESTRATOR_BOT_TOKEN not found in .env")

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    print(f"[*] Sending: '{text[:50]}...'")

    time.sleep(delay)  # Rate limit protection

    try:
        response = requests.post(url, json={
            "chat_id": ADMIN_CHAT_ID,
            "text": text
        }, timeout=10)

        response.raise_for_status()
        result = response.json()

        if result.get("ok"):
            print(f"[OK] Message sent successfully (ID: {result['result']['message_id']})")
        else:
            print(f"[ERROR] Failed to send: {result}")

        return result

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Request failed: {e}")
        return {"ok": False, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(
        description="Send test messages to RIVET CEO Bot"
    )

    parser.add_argument(
        "--custom",
        type=str,
        help="Send a custom message instead of predefined tests"
    )

    parser.add_argument(
        "--delay",
        type=float,
        default=2.0,
        help="Delay between messages in seconds (default: 2.0)"
    )

    args = parser.parse_args()

    print("=" * 60)
    print(f"[TEST] RIVET CEO Bot Test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"[TEST] Target: {ADMIN_CHAT_ID}")
    print("=" * 60)
    print()

    # Send custom message or predefined tests
    if args.custom:
        queries = [args.custom]
    else:
        queries = TEST_QUERIES

    results = []

    for i, query in enumerate(queries, 1):
        print(f"\n[{i}/{len(queries)}]")
        result = send_test_message(query, delay=args.delay if i > 1 else 0)
        results.append({
            "query": query,
            "success": result.get("ok", False),
            "message_id": result.get("result", {}).get("message_id"),
            "timestamp": datetime.now().isoformat()
        })

    # Summary
    print()
    print("=" * 60)
    print("[SUMMARY]")
    print(f"  Total queries: {len(results)}")
    print(f"  Successful: {sum(1 for r in results if r['success'])}")
    print(f"  Failed: {sum(1 for r in results if not r['success'])}")
    print("=" * 60)
    print()
    print("[NEXT STEPS]")
    print("  1. Wait 15-30 seconds for bot to process")
    print("  2. Run: python scripts/pull_langsmith_runs.py --project rivet-ceo-bot --limit 10")
    print("  3. Check: evals/langsmith/runs/*.md for traces")

    return 0 if all(r['success'] for r in results) else 1


if __name__ == "__main__":
    exit(main())

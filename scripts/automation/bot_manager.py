#!/usr/bin/env python3
"""
Telegram Bot Manager - Singleton CLI tool for managing the bot.

Commands:
    start   - Start the bot (fails if already running)
    stop    - Stop the running bot
    restart - Stop then start the bot
    status  - Check if bot is running (with health check)

Usage:
    python scripts/bot_manager.py start
    python scripts/bot_manager.py stop
    python scripts/bot_manager.py restart
    python scripts/bot_manager.py status

This is the ONLY way to run the bot in production. All other entry points
are deprecated to prevent instance conflicts.
"""

import sys
import os
import asyncio
import signal
import subprocess
from pathlib import Path
from typing import Optional
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agent_factory.integrations.telegram.singleton import (
    BotLock,
    BotLockError,
    check_bot_running,
    force_release_lock
)


def print_banner():
    """Print CLI banner."""
    print("=" * 60)
    print("Agent Factory Telegram Bot Manager")
    print("=" * 60)


def check_health() -> Optional[dict]:
    """
    Check bot health via HTTP endpoint.

    Returns:
        Health info dict if bot is healthy, None if unreachable

    Example:
        {'status': 'running', 'pid': 12345, 'uptime_seconds': 3600}
    """
    try:
        import requests
        response = requests.get("http://localhost:9876/health", timeout=2)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return None


def get_bot_pid() -> Optional[int]:
    """
    Get PID of running bot process.

    Returns:
        PID if bot is running, None otherwise

    Uses health endpoint for reliable PID info.
    """
    health = check_health()
    if health:
        return health.get('pid')
    return None


def kill_bot_process():
    """
    Kill bot process by PID.

    Uses health endpoint to get PID, then sends SIGTERM.
    Falls back to force kill if needed.
    """
    pid = get_bot_pid()
    if pid is None:
        print("⚠️ Cannot find bot PID (health endpoint unreachable)")
        print("Trying to force release lock...")
        force_release_lock()
        return

    print(f"Found bot process: PID {pid}")
    print("Sending SIGTERM...")

    try:
        if sys.platform == "win32":
            # Windows: Use taskkill
            subprocess.run(["taskkill", "/F", "/PID", str(pid)], check=True)
        else:
            # Unix: Send SIGTERM
            os.kill(pid, signal.SIGTERM)

        print(f"✅ Bot stopped (PID {pid})")

    except Exception as e:
        print(f"❌ Failed to kill process: {e}")
        print("Trying to force release lock...")
        force_release_lock()


def cmd_start():
    """Start the bot."""
    print_banner()
    print("Command: START")
    print("=" * 60)

    # Check if already running
    if check_bot_running():
        health = check_health()
        if health:
            print(f"❌ Bot is already running!")
            print(f"   PID: {health.get('pid')}")
            print(f"   Uptime: {health.get('uptime_seconds', 0):.0f} seconds")
            print()
            print("To stop the bot:")
            print("  python scripts/bot_manager.py stop")
            sys.exit(1)
        else:
            print("⚠️ Lock file exists but bot is not responding")
            print("This may be a stale lock from a crashed instance")
            print()
            response = input("Force release lock and start? (y/N): ")
            if response.lower() != 'y':
                print("Aborted")
                sys.exit(1)
            force_release_lock()

    # Start bot
    print("Starting bot...")
    print()

    try:
        # Import and run bot with lock
        from agent_factory.integrations.telegram.config import TelegramConfig
        from agent_factory.integrations.telegram.bot import TelegramBot

        config = TelegramConfig.from_env()

        # Acquire lock before starting
        with BotLock() as lock:
            print(f"Bot Token: {config.bot_token[:20]}...")
            print(f"Bot Username: @Agent_Factory_Bot")
            print("=" * 60)
            print()

            bot = TelegramBot(config)
            asyncio.run(bot.run())

    except BotLockError as e:
        print(str(e))
        sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n✅ Bot stopped (Ctrl+C)")

    except Exception as e:
        print(f"\n❌ Bot crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def cmd_stop():
    """Stop the bot."""
    print_banner()
    print("Command: STOP")
    print("=" * 60)

    if not check_bot_running():
        print("ℹ️ Bot is not running")
        sys.exit(0)

    print("Stopping bot...")
    kill_bot_process()


def cmd_restart():
    """Restart the bot."""
    print_banner()
    print("Command: RESTART")
    print("=" * 60)

    # Stop if running
    if check_bot_running():
        print("Stopping existing instance...")
        kill_bot_process()

        # Wait for shutdown
        print("Waiting for shutdown...")
        import time
        for i in range(10):
            if not check_bot_running():
                break
            time.sleep(1)
        else:
            print("⚠️ Bot did not stop cleanly, forcing...")
            force_release_lock()

    # Start fresh
    print()
    print("Starting bot...")
    cmd_start()


def cmd_status():
    """Check bot status."""
    print_banner()
    print("Command: STATUS")
    print("=" * 60)

    # Check lock file
    lock_exists = check_bot_running()
    print(f"Lock file: {'EXISTS' if lock_exists else 'NOT FOUND'}")

    # Check health endpoint
    health = check_health()
    if health:
        print(f"Health endpoint: ✅ RESPONDING")
        print(f"  PID: {health.get('pid')}")
        print(f"  Status: {health.get('status')}")
        uptime = health.get('uptime_seconds', 0)
        print(f"  Uptime: {uptime:.0f} seconds ({uptime/60:.1f} minutes)")
    else:
        print(f"Health endpoint: ❌ NOT RESPONDING")

    # Overall status
    print()
    if lock_exists and health:
        print("✅ Bot is RUNNING")
    elif lock_exists and not health:
        print("⚠️ Bot may be STARTING or STUCK")
        print("   Lock file exists but health endpoint not responding")
    elif not lock_exists and health:
        print("⚠️ Bot is RUNNING but no lock file")
        print("   This should not happen!")
    else:
        print("❌ Bot is NOT RUNNING")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print_banner()
        print("Usage: python scripts/bot_manager.py <command>")
        print()
        print("Commands:")
        print("  start   - Start the bot")
        print("  stop    - Stop the bot")
        print("  restart - Restart the bot")
        print("  status  - Check bot status")
        print()
        print("Examples:")
        print("  python scripts/bot_manager.py start")
        print("  python scripts/bot_manager.py status")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "start":
        cmd_start()
    elif command == "stop":
        cmd_stop()
    elif command == "restart":
        cmd_restart()
    elif command == "status":
        cmd_status()
    else:
        print(f"❌ Unknown command: {command}")
        print("Valid commands: start, stop, restart, status")
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Push URLs to VPS KB Factory Redis Queue

Usage:
    python scripts/push_urls_to_vps.py           # Push all URLs
    python scripts/push_urls_to_vps.py --dry-run # Show what would be pushed
    python scripts/push_urls_to_vps.py --check   # Check queue status only
"""

import argparse
import subprocess
import sys
import os

# Add scripts directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kb_seed_urls import SEED_URLS, URL_METADATA

VPS_IP = "72.60.175.144"
VPS_USER = "root"
REDIS_QUEUE = "kb_ingest_jobs"


def run_ssh_command(command: str, capture_output: bool = True) -> str:
    """Execute command on VPS via SSH."""
    ssh_cmd = f'ssh {VPS_USER}@{VPS_IP} "{command}"'
    try:
        result = subprocess.run(
            ssh_cmd,
            shell=True,
            capture_output=capture_output,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            print(f"[ERROR] SSH command failed: {result.stderr}")
            return ""
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        print("[ERROR] SSH command timed out")
        return ""
    except Exception as e:
        print(f"[ERROR] SSH failed: {e}")
        return ""


def get_queue_length() -> int:
    """Get current length of Redis queue."""
    output = run_ssh_command(f"docker exec infra_redis_1 redis-cli LLEN {REDIS_QUEUE}")
    try:
        return int(output)
    except ValueError:
        return -1


def get_atom_count() -> int:
    """Get current atom count in PostgreSQL."""
    output = run_ssh_command(
        "docker exec infra_postgres_1 psql -U rivet -d rivet -t -c 'SELECT COUNT(*) FROM knowledge_atoms;'"
    )
    try:
        return int(output.strip())
    except ValueError:
        return -1


def push_url_to_queue(url: str) -> bool:
    """Push a single URL to the Redis queue."""
    # Escape URL for shell
    escaped_url = url.replace("'", "'\\''")
    output = run_ssh_command(
        f"docker exec infra_redis_1 redis-cli RPUSH {REDIS_QUEUE} '{escaped_url}'"
    )
    return output.isdigit()


def check_status():
    """Check VPS KB Factory status."""
    print("=" * 60)
    print("VPS KB Factory Status Check")
    print("=" * 60)
    print(f"VPS: {VPS_IP}")
    print()

    # Queue length
    queue_len = get_queue_length()
    if queue_len >= 0:
        print(f"[OK] Redis queue length: {queue_len}")
    else:
        print("[ERROR] Could not connect to Redis")

    # Atom count
    atom_count = get_atom_count()
    if atom_count >= 0:
        print(f"[OK] Knowledge atoms in DB: {atom_count}")
    else:
        print("[ERROR] Could not connect to PostgreSQL")

    print("=" * 60)
    return queue_len >= 0 and atom_count >= 0


def push_urls(dry_run: bool = False):
    """Push all seed URLs to VPS Redis queue."""
    print("=" * 60)
    print("Push URLs to VPS KB Factory")
    print("=" * 60)
    print(f"VPS: {VPS_IP}")
    print(f"URLs to push: {len(SEED_URLS)}")
    print()

    if dry_run:
        print("[DRY RUN] Would push these URLs:")
        for i, url in enumerate(SEED_URLS, 1):
            print(f"  {i}. {url}")
        return

    # Check connectivity first
    print("Checking VPS connectivity...")
    initial_queue = get_queue_length()
    if initial_queue < 0:
        print("[ERROR] Cannot connect to VPS. Check SSH access.")
        sys.exit(1)

    print(f"[OK] Initial queue length: {initial_queue}")
    print()

    # Push URLs
    success = 0
    failed = 0

    for i, url in enumerate(SEED_URLS, 1):
        print(f"[{i}/{len(SEED_URLS)}] Pushing: {url[:60]}...")
        if push_url_to_queue(url):
            success += 1
            print(f"        [OK]")
        else:
            failed += 1
            print(f"        [FAILED]")

    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"  Pushed: {success}")
    print(f"  Failed: {failed}")

    # Final queue check
    final_queue = get_queue_length()
    print(f"  Queue length now: {final_queue}")
    print("=" * 60)

    if failed > 0:
        print("\n[WARNING] Some URLs failed to push. Check VPS connectivity.")
    else:
        print("\n[SUCCESS] All URLs pushed! Worker will process them automatically.")
        print("\nMonitor progress with:")
        print("  python scripts/monitor_vps_ingestion.py")


def main():
    parser = argparse.ArgumentParser(description="Push URLs to VPS KB Factory")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be pushed")
    parser.add_argument("--check", action="store_true", help="Check status only")
    args = parser.parse_args()

    if args.check:
        check_status()
    elif args.dry_run:
        push_urls(dry_run=True)
    else:
        push_urls(dry_run=False)


if __name__ == "__main__":
    main()

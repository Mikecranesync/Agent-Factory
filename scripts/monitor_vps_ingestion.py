#!/usr/bin/env python3
"""
Monitor VPS KB Factory Ingestion Progress

Usage:
    python scripts/monitor_vps_ingestion.py           # One-time status check
    python scripts/monitor_vps_ingestion.py --watch   # Continuous monitoring
    python scripts/monitor_vps_ingestion.py --logs    # Show worker logs
"""

import argparse
import subprocess
import sys
import time

VPS_IP = "72.60.175.144"
VPS_USER = "root"
REDIS_QUEUE = "kb_ingest_jobs"


def run_ssh_command(command: str) -> str:
    """Execute command on VPS via SSH."""
    ssh_cmd = f'ssh {VPS_USER}@{VPS_IP} "{command}"'
    try:
        result = subprocess.run(
            ssh_cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout.strip()
    except Exception as e:
        return f"ERROR: {e}"


def get_queue_length() -> int:
    """Get Redis queue length."""
    output = run_ssh_command(f"docker exec infra_redis_1 redis-cli LLEN {REDIS_QUEUE}")
    try:
        return int(output)
    except ValueError:
        return -1


def get_atom_count() -> int:
    """Get knowledge atom count."""
    output = run_ssh_command(
        "docker exec infra_postgres_1 psql -U rivet -d rivet -t -c 'SELECT COUNT(*) FROM knowledge_atoms;'"
    )
    try:
        return int(output.strip())
    except ValueError:
        return -1


def get_recent_atoms(limit: int = 5) -> str:
    """Get most recently created atoms."""
    output = run_ssh_command(
        f"docker exec infra_postgres_1 psql -U rivet -d rivet -t -c "
        f"\\\"SELECT atom_type, LEFT(title, 50) as title FROM knowledge_atoms ORDER BY created_at DESC LIMIT {limit};\\\""
    )
    return output


def get_worker_status() -> str:
    """Check if worker is running."""
    output = run_ssh_command("docker ps --filter name=rivet-worker --format '{{.Status}}'")
    return output if output else "Not running"


def get_worker_logs(lines: int = 30) -> str:
    """Get recent worker logs."""
    output = run_ssh_command(f"docker logs infra_rivet-worker_1 --tail {lines} 2>&1")
    return output


def show_status():
    """Display current ingestion status."""
    print("=" * 60)
    print("VPS KB Factory Ingestion Status")
    print("=" * 60)
    print(f"VPS: {VPS_IP}")
    print()

    # Worker status
    worker_status = get_worker_status()
    status_icon = "[OK]" if "Up" in worker_status else "[!!]"
    print(f"{status_icon} Worker: {worker_status}")

    # Queue
    queue_len = get_queue_length()
    if queue_len >= 0:
        print(f"[OK] Queue: {queue_len} URLs pending")
    else:
        print("[!!] Queue: Cannot connect")

    # Atoms
    atom_count = get_atom_count()
    if atom_count >= 0:
        print(f"[OK] Atoms: {atom_count} in database")
    else:
        print("[!!] Atoms: Cannot connect")

    print()

    # Recent atoms
    if atom_count > 0:
        print("Recent atoms:")
        recent = get_recent_atoms()
        if recent:
            for line in recent.split('\n')[:5]:
                if line.strip():
                    print(f"  {line.strip()}")
        else:
            print("  (none)")

    print("=" * 60)
    return queue_len, atom_count


def watch_mode(interval: int = 30):
    """Continuous monitoring mode."""
    print(f"Watching VPS ingestion (refresh every {interval}s)")
    print("Press Ctrl+C to stop")
    print()

    prev_atoms = 0
    try:
        while True:
            queue_len, atom_count = show_status()

            # Show progress
            if atom_count > prev_atoms:
                new_atoms = atom_count - prev_atoms
                print(f"[+] {new_atoms} new atoms since last check")
            prev_atoms = atom_count

            # Check if done
            if queue_len == 0:
                print("\n[DONE] Queue is empty - ingestion complete!")
                break

            print(f"\nNext refresh in {interval}s...")
            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")


def show_logs(lines: int = 50):
    """Show worker logs."""
    print("=" * 60)
    print("Worker Logs (last 50 lines)")
    print("=" * 60)
    logs = get_worker_logs(lines)
    print(logs)
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Monitor VPS KB Factory")
    parser.add_argument("--watch", action="store_true", help="Continuous monitoring")
    parser.add_argument("--logs", action="store_true", help="Show worker logs")
    parser.add_argument("--interval", type=int, default=30, help="Watch interval (seconds)")
    args = parser.parse_args()

    if args.logs:
        show_logs()
    elif args.watch:
        watch_mode(args.interval)
    else:
        show_status()


if __name__ == "__main__":
    main()

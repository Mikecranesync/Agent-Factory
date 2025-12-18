#!/usr/bin/env python3
"""
Migration script to tag existing manual tasks with user-action label.

Scans all "To Do" tasks for keywords indicating manual human execution
(signup, payment, api key, etc.) and tags them with the user-action label.

Usage:
    poetry run python scripts/backlog/migrate_user_actions.py --dry-run
    poetry run python scripts/backlog/migrate_user_actions.py
"""

import argparse
import subprocess
from pathlib import Path
from typing import List, Dict, Set


# Keywords indicating manual user action required
MANUAL_KEYWORDS = {
    # Cloud services
    "signup", "sign up", "create account", "register account",
    "railway", "supabase", "neon", "vercel", "render", "fly.io",

    # API/Authentication
    "api key", "api_key", "apikey", "oauth", "access token",
    "client id", "client secret", "credentials",

    # Payment/Billing
    "payment", "subscription", "billing", "credit card",
    "upgrade plan", "purchase",

    # Manual setup
    "voice recording", "record voice", "voice sample",
    "manual setup", "configure manually", "human approval",
    "review", "approve", "authorize",

    # Device/Hardware
    "install software", "download", "physical device",
    "connect hardware", "usb", "serial port",

    # Other manual actions
    "phone call", "email", "meeting", "schedule",
    "user input required", "manual intervention"
}


def get_repo_root() -> Path:
    """Get repository root directory."""
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        shell=True
    )
    return Path(result.stdout.strip())


def get_all_todo_tasks() -> List[Dict]:
    """Get all tasks with status 'To Do' from Backlog CLI."""
    result = subprocess.run(
        ["backlog", "task", "list", "--status", "To Do", "--plain"],
        capture_output=True,
        text=True,
        shell=True
    )

    tasks = []
    for line in result.stdout.strip().split("\n"):
        if not line.strip():
            continue

        # Parse: "[STATUS] task-id - Title"
        import re
        match = re.match(r'\s*(?:\[([A-Z]+)\]\s+)?(task-[^\s]+)\s+-\s+(.+)', line)
        if match:
            status, task_id, title = match.groups()
            tasks.append({
                "id": task_id,
                "title": title,
                "status": status or "To Do"
            })

    return tasks


def read_task_file(task_id: str) -> str:
    """Read task file content."""
    repo_root = get_repo_root()
    task_files = list((repo_root / "backlog" / "tasks").glob(f"{task_id} - *.md"))

    if not task_files:
        return ""

    return task_files[0].read_text(encoding='utf-8')


def get_task_labels(task_id: str) -> Set[str]:
    """Extract labels from task YAML frontmatter."""
    content = read_task_file(task_id)
    if not content:
        return set()

    # Extract labels from YAML
    labels = set()
    in_labels_section = False

    for line in content.split("\n"):
        if line.strip() == "labels:":
            in_labels_section = True
            continue

        if in_labels_section:
            if line.startswith("  - "):
                label = line.strip()[2:].strip()
                labels.add(label)
            elif not line.startswith(" ") and line.strip():
                # End of labels section
                break

    return labels


def has_manual_keyword(task_id: str, title: str) -> bool:
    """Check if task contains manual action keywords."""
    content = read_task_file(task_id)
    full_text = (title + " " + content).lower()

    for keyword in MANUAL_KEYWORDS:
        if keyword in full_text:
            return True

    return False


def already_has_user_action_label(task_id: str) -> bool:
    """Check if task already has user-action label."""
    labels = get_task_labels(task_id)
    return "user-action" in labels


def add_user_action_label(task_id: str) -> bool:
    """Add user-action label to task via CLI."""
    # Get existing labels
    existing_labels = get_task_labels(task_id)
    existing_labels.add("user-action")

    # Build labels string
    labels_str = ",".join(sorted(existing_labels))

    # Update task
    result = subprocess.run(
        ["backlog", "task", "edit", task_id, "--labels", labels_str],
        capture_output=True,
        text=True,
        shell=True
    )

    return result.returncode == 0


def scan_tasks(dry_run: bool = True) -> List[Dict]:
    """
    Scan all To Do tasks for manual keywords.

    Returns list of tasks that should be tagged with user-action label.
    """
    print("\n" + "=" * 60)
    print("Scanning To Do tasks for manual keywords...")
    print("=" * 60 + "\n")

    all_tasks = get_all_todo_tasks()
    print(f"Found {len(all_tasks)} To Do tasks")

    candidates = []

    for task in all_tasks:
        task_id = task["id"]
        title = task["title"]

        # Skip if already has user-action label
        if already_has_user_action_label(task_id):
            print(f"[SKIP] {task_id}: Already has user-action label")
            continue

        # Check for manual keywords
        if has_manual_keyword(task_id, title):
            candidates.append(task)
            print(f"[MATCH] {task_id}: {title}")
        else:
            print(f"[NO MATCH] {task_id}: {title}")

    print(f"\n{len(candidates)} task(s) need user-action label")
    return candidates


def migrate_tasks(candidates: List[Dict], dry_run: bool = True) -> None:
    """Tag candidate tasks with user-action label."""
    if not candidates:
        print("\nNo tasks to migrate.")
        return

    print("\n" + "=" * 60)
    if dry_run:
        print("DRY RUN - Preview Changes")
    else:
        print("Applying user-action Labels")
    print("=" * 60 + "\n")

    for task in candidates:
        task_id = task["id"]
        title = task["title"]

        if dry_run:
            print(f"[DRY RUN] Would tag {task_id}: {title}")
        else:
            success = add_user_action_label(task_id)
            if success:
                print(f"[OK] Tagged {task_id}: {title}")
            else:
                print(f"[ERROR] Failed to tag {task_id}")

    if dry_run:
        print("\n" + "=" * 60)
        print("This was a DRY RUN - no changes were made")
        print("Run without --dry-run to apply changes")
        print("=" * 60)


def confirm_migration(candidates: List[Dict]) -> bool:
    """Ask user to confirm migration."""
    print("\n" + "=" * 60)
    print(f"Ready to tag {len(candidates)} task(s) with user-action label")
    print("=" * 60 + "\n")

    for task in candidates:
        print(f"  - {task['id']}: {task['title']}")

    print("\nProceed? (yes/no): ", end="")
    response = input().strip().lower()

    return response in ["yes", "y"]


def main():
    parser = argparse.ArgumentParser(
        description="Tag existing manual tasks with user-action label"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without applying them"
    )

    args = parser.parse_args()

    # Scan for candidates
    candidates = scan_tasks(dry_run=args.dry_run)

    if not candidates:
        print("\n[OK] No tasks need user-action label")
        return

    # Dry run: preview only
    if args.dry_run:
        migrate_tasks(candidates, dry_run=True)
        return

    # Confirm before applying
    if not confirm_migration(candidates):
        print("\n[CANCELLED] No changes were made")
        return

    # Apply changes
    migrate_tasks(candidates, dry_run=False)

    print("\n" + "=" * 60)
    print("[OK] Migration complete")
    print("=" * 60)
    print("\nRun sync to update TASK.md:")
    print("  poetry run python scripts/backlog/sync_tasks.py")


if __name__ == "__main__":
    main()

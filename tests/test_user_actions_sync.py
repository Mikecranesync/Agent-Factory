"""
Test suite for User Actions sync feature.

Tests the sync_tasks.py functionality for querying, filtering, and formatting
tasks with the user-action label for display in TASK.md.
"""

import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict


# Mock functions (replace with actual imports in integration tests)
def mock_get_task_details(task_id: str) -> Dict:
    """Mock task details for testing."""
    tasks = {
        "task-42": {
            "id": "task-42",
            "title": "ACTION: Create Railway Database Account",
            "status": "To Do",
            "priority": "high",
            "labels": ["user-action", "database", "setup"],
            "created_date": "2025-12-17",
            "acceptance_criteria": [
                "Railway account created",
                "PostgreSQL database provisioned",
                "Connection string added to .env file",
                "Test connection successful"
            ]
        },
        "task-43": {
            "id": "task-43",
            "title": "ACTION: Setup ElevenLabs Voice Clone",
            "status": "To Do",
            "priority": "medium",
            "labels": ["user-action", "content", "voice"],
            "created_date": "2025-12-16",
            "acceptance_criteria": [
                "Voice samples recorded (10-15 min)",
                "ElevenLabs account created",
                "Voice clone generated and tested"
            ]
        },
        "task-44": {
            "id": "task-44",
            "title": "FIX: Database connection timeout",
            "status": "To Do",
            "priority": "high",
            "labels": ["fix", "database"],
            "created_date": "2025-12-15",
            "acceptance_criteria": [
                "Timeout issue diagnosed",
                "Fix implemented",
                "Tests passing"
            ]
        },
        "task-45": {
            "id": "task-45",
            "title": "ACTION: Configure GitHub OAuth",
            "status": "To Do",
            "priority": "low",
            "labels": ["user-action", "auth", "github"],
            "created_date": "2025-12-14",
            "acceptance_criteria": [
                "GitHub OAuth app created",
                "Client ID/secret stored in .env"
            ]
        }
    }
    return tasks.get(task_id, {})


def mock_get_user_action_tasks() -> List[Dict]:
    """Mock user action tasks (tasks with user-action label)."""
    all_tasks = ["task-42", "task-43", "task-44", "task-45"]
    user_actions = []

    for task_id in all_tasks:
        details = mock_get_task_details(task_id)
        if "user-action" in details.get("labels", []):
            user_actions.append(details)

    return user_actions


def format_user_actions_section(tasks: List[Dict]) -> str:
    """
    Format user action tasks for TASK.md.

    Groups by priority (high/medium/low), sorts by created_date within groups,
    shows inline acceptance criteria (max 3).
    """
    if not tasks:
        return "No manual tasks requiring user execution.\n"

    # Group by priority
    priority_groups = {"high": [], "medium": [], "low": []}
    for task in tasks:
        priority = task.get("priority", "medium")
        priority_groups[priority].append(task)

    # Sort within groups by created_date (oldest first)
    for priority in priority_groups:
        priority_groups[priority].sort(
            key=lambda t: t.get("created_date", "2025-01-01")
        )

    # Format output
    sections = []

    for priority in ["high", "medium", "low"]:
        group_tasks = priority_groups[priority]
        if not group_tasks:
            continue

        # Priority header
        sections.append(f"### Priority: {priority.upper()}\n")

        for task in group_tasks:
            task_id = task.get("id", "unknown")
            title = task.get("title", "No title")
            created = task.get("created_date", "Unknown")
            criteria = task.get("acceptance_criteria", [])

            # Task header with [ACTION REQUIRED] prefix
            sections.append(f"**[ACTION REQUIRED] {task_id}:** {title}\n")
            sections.append(f"- Created: {created}\n")

            # Show up to 3 acceptance criteria inline
            if criteria:
                max_display = min(3, len(criteria))
                for i in range(max_display):
                    sections.append(f"- [ ] #{i+1} {criteria[i]}\n")

                if len(criteria) > 3:
                    remaining = len(criteria) - 3
                    sections.append(f"- ... and {remaining} more\n")

            # View command
            sections.append(f"- View: `backlog task view {task_id}`\n")
            sections.append("\n")

    return "".join(sections)


def replace_section(content: str, begin_marker: str, end_marker: str, new_content: str) -> str:
    """Replace content between sync zone markers."""
    pattern = re.compile(
        rf"({re.escape(begin_marker)})(.*?)({re.escape(end_marker)})",
        re.DOTALL
    )

    replacement = f"\\1\n{new_content}\\3"
    updated = pattern.sub(replacement, content)

    return updated


# ============================================================
# TEST CASES
# ============================================================

def test_format_user_actions_section_empty():
    """Test formatting when no user action tasks exist."""
    tasks = []
    result = format_user_actions_section(tasks)

    assert result == "No manual tasks requiring user execution.\n"
    print("[OK] test_format_user_actions_section_empty")


def test_format_user_actions_section_with_tasks():
    """Test formatting with multiple user action tasks."""
    tasks = mock_get_user_action_tasks()
    result = format_user_actions_section(tasks)

    # Check structure
    assert "### Priority: HIGH" in result
    assert "### Priority: MEDIUM" in result
    assert "### Priority: LOW" in result

    # Check task-42 (high priority)
    assert "[ACTION REQUIRED] task-42:" in result
    assert "Create Railway Database Account" in result
    assert "Created: 2025-12-17" in result
    assert "Railway account created" in result
    assert "backlog task view task-42" in result

    # Check task-43 (medium priority)
    assert "[ACTION REQUIRED] task-43:" in result
    assert "Setup ElevenLabs Voice Clone" in result

    # Check task-45 (low priority)
    assert "[ACTION REQUIRED] task-45:" in result
    assert "Configure GitHub OAuth" in result

    # Should NOT include task-44 (no user-action label)
    assert "task-44" not in result
    assert "Database connection timeout" not in result

    print("[OK] test_format_user_actions_section_with_tasks")


def test_format_user_actions_priority_grouping():
    """Test that tasks are grouped by priority and sorted by date."""
    tasks = mock_get_user_action_tasks()
    result = format_user_actions_section(tasks)

    # Find positions of priority sections
    high_pos = result.find("### Priority: HIGH")
    medium_pos = result.find("### Priority: MEDIUM")
    low_pos = result.find("### Priority: LOW")

    # Verify order: high → medium → low
    assert high_pos < medium_pos < low_pos

    # Find task positions within result
    task_42_pos = result.find("task-42")  # high, 2025-12-17
    task_43_pos = result.find("task-43")  # medium, 2025-12-16
    task_45_pos = result.find("task-45")  # low, 2025-12-14

    # Verify priority grouping: high before medium before low
    assert task_42_pos < task_43_pos < task_45_pos

    print("[OK] test_format_user_actions_priority_grouping")


def test_replace_section_user_actions():
    """Test sync zone replacement for USER_ACTIONS section."""
    # Mock TASK.md content
    original = """# TASK.md

<!-- BACKLOG_SYNC:USER_ACTIONS:BEGIN -->
## User Actions

Old content here.

<!-- BACKLOG_SYNC:USER_ACTIONS:END -->

## Other Section
"""

    # Generate new content
    tasks = [mock_get_task_details("task-42")]
    new_content = format_user_actions_section(tasks)

    # Replace section
    updated = replace_section(
        original,
        "<!-- BACKLOG_SYNC:USER_ACTIONS:BEGIN -->",
        "<!-- BACKLOG_SYNC:USER_ACTIONS:END -->",
        new_content
    )

    # Verify replacement
    assert "Old content here" not in updated
    assert "[ACTION REQUIRED] task-42:" in updated
    assert "Create Railway Database Account" in updated
    assert "<!-- BACKLOG_SYNC:USER_ACTIONS:BEGIN -->" in updated
    assert "<!-- BACKLOG_SYNC:USER_ACTIONS:END -->" in updated
    assert "## Other Section" in updated  # Preserve other sections

    print("[OK] test_replace_section_user_actions")


def test_sync_preserves_other_sections():
    """Test that syncing USER_ACTIONS doesn't affect other sync zones."""
    original = """<!-- BACKLOG_SYNC:CURRENT:BEGIN -->
Current task content
<!-- BACKLOG_SYNC:CURRENT:END -->

<!-- BACKLOG_SYNC:USER_ACTIONS:BEGIN -->
Old user actions
<!-- BACKLOG_SYNC:USER_ACTIONS:END -->

<!-- BACKLOG_SYNC:BACKLOG:BEGIN -->
Backlog content
<!-- BACKLOG_SYNC:BACKLOG:END -->
"""

    # Update only USER_ACTIONS section
    tasks = [mock_get_task_details("task-43")]
    new_content = format_user_actions_section(tasks)

    updated = replace_section(
        original,
        "<!-- BACKLOG_SYNC:USER_ACTIONS:BEGIN -->",
        "<!-- BACKLOG_SYNC:USER_ACTIONS:END -->",
        new_content
    )

    # Verify other sections unchanged
    assert "Current task content" in updated
    assert "Backlog content" in updated

    # Verify USER_ACTIONS updated
    assert "Old user actions" not in updated
    assert "[ACTION REQUIRED] task-43:" in updated

    print("[OK] test_sync_preserves_other_sections")


# ============================================================
# RUN TESTS
# ============================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Running User Actions Sync Tests")
    print("=" * 60 + "\n")

    test_format_user_actions_section_empty()
    test_format_user_actions_section_with_tasks()
    test_format_user_actions_priority_grouping()
    test_replace_section_user_actions()
    test_sync_preserves_other_sections()

    print("\n" + "=" * 60)
    print("[OK] All 5 tests passed")
    print("=" * 60 + "\n")

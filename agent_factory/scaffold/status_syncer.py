"""SCAFFOLD Platform - Backlog Status Syncer

Auto-updates Backlog.md task status after PR creation.

Features:
- Marks task as In Progress when execution starts
- Marks task as Done when PR is created
- Adds PR URL to task notes
- Syncs to TASK.md automatically

Example:
    >>> syncer = StatusSyncer()
    >>> syncer.sync_status("task-123", "Done", pr_url="https://github.com/user/repo/pull/42")
    >>> # Task status updated in Backlog.md and TASK.md
"""

import logging
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class StatusSyncerError(Exception):
    """Base exception for StatusSyncer errors."""
    pass


class StatusSyncer:
    """Sync task status to Backlog.md after PR creation.

    Updates task metadata automatically:
    - Sets status (To Do, In Progress, Done)
    - Adds PR URL to notes
    - Triggers TASK.md sync
    """

    def __init__(self, repo_root: Optional[Path] = None):
        """Initialize StatusSyncer.

        Args:
            repo_root: Repository root (defaults to cwd)
        """
        self.repo_root = Path(repo_root) if repo_root else Path.cwd()
        self.sync_script = self.repo_root / "scripts" / "backlog" / "sync_tasks.py"

    def sync_status(
        self,
        task_id: str,
        new_status: str,
        pr_url: Optional[str] = None
    ) -> bool:
        """Update task status in Backlog.md.

        Args:
            task_id: Task identifier (e.g., "task-scaffold-pr-creation")
            new_status: New status ("To Do", "In Progress", or "Done")
            pr_url: Optional PR URL to add to notes

        Returns:
            True if sync succeeded, False otherwise

        Raises:
            StatusSyncerError: If critical sync failure
        """
        logger.info(f"Syncing task {task_id} status to '{new_status}'")

        try:
            # Update task status
            self._update_status(task_id, new_status)

            # Add PR URL to notes if provided
            if pr_url:
                self._add_pr_url(task_id, pr_url)

            # Sync to TASK.md
            self._sync_task_md()

            logger.info(f"Task {task_id} status synced successfully")
            return True

        except Exception as e:
            # Log warning but don't fail - sync is not critical
            logger.warning(f"Status sync failed for task {task_id}: {e}")
            return False

    def mark_in_progress(self, task_id: str) -> bool:
        """Mark task as In Progress.

        Args:
            task_id: Task identifier

        Returns:
            True if successful
        """
        return self.sync_status(task_id, "In Progress")

    def mark_done(self, task_id: str, pr_url: Optional[str] = None) -> bool:
        """Mark task as Done.

        Args:
            task_id: Task identifier
            pr_url: Optional PR URL

        Returns:
            True if successful
        """
        return self.sync_status(task_id, "Done", pr_url=pr_url)

    def _update_status(self, task_id: str, new_status: str):
        """Update task status using backlog CLI.

        Args:
            task_id: Task identifier
            new_status: New status value

        Raises:
            StatusSyncerError: If status update fails
        """
        result = subprocess.run(
            ["backlog", "task", "edit", task_id, "--status", new_status],
            cwd=self.repo_root,
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            raise StatusSyncerError(
                f"Failed to update status: {result.stderr}"
            )

        logger.debug(f"Task {task_id} status set to '{new_status}'")

    def _add_pr_url(self, task_id: str, pr_url: str):
        """Add PR URL to task notes.

        Args:
            task_id: Task identifier
            pr_url: PR URL to add

        Raises:
            StatusSyncerError: If note addition fails
        """
        note = f"PR: {pr_url}"

        result = subprocess.run(
            ["backlog", "task", "edit", task_id, "--notes-append", note],
            cwd=self.repo_root,
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            raise StatusSyncerError(
                f"Failed to add PR URL: {result.stderr}"
            )

        logger.debug(f"Added PR URL to task {task_id}: {pr_url}")

    def _sync_task_md(self):
        """Sync changes to TASK.md using sync_tasks.py.

        Raises:
            StatusSyncerError: If TASK.md sync fails
        """
        if not self.sync_script.exists():
            logger.warning(f"Sync script not found: {self.sync_script}")
            return

        result = subprocess.run(
            ["poetry", "run", "python", str(self.sync_script)],
            cwd=self.repo_root,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            raise StatusSyncerError(
                f"TASK.md sync failed: {result.stderr}"
            )

        logger.debug("TASK.md synced successfully")


def create_status_syncer(repo_root: Optional[Path] = None) -> StatusSyncer:
    """Factory function to create StatusSyncer.

    Args:
        repo_root: Repository root (defaults to cwd)

    Returns:
        StatusSyncer instance
    """
    return StatusSyncer(repo_root=repo_root)

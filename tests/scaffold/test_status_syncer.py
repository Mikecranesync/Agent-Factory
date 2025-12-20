"""Tests for StatusSyncer - Backlog Status Synchronization

Tests cover:
- Initialization
- Status updates (To Do, In Progress, Done)
- PR URL tracking
- TASK.md sync
- Error handling
- Convenience methods
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import subprocess

from agent_factory.scaffold.status_syncer import (
    StatusSyncer,
    StatusSyncerError,
    create_status_syncer
)


# ============================================================================
# INITIALIZATION TESTS
# ============================================================================

def test_init_default():
    """Test StatusSyncer initialization with defaults."""
    syncer = StatusSyncer()

    assert syncer.repo_root == Path.cwd()
    assert syncer.sync_script == Path.cwd() / "scripts" / "backlog" / "sync_tasks.py"


def test_init_custom_repo():
    """Test StatusSyncer with custom repo root."""
    custom_root = Path("/custom/repo")
    syncer = StatusSyncer(repo_root=custom_root)

    assert syncer.repo_root == custom_root
    assert syncer.sync_script == custom_root / "scripts" / "backlog" / "sync_tasks.py"


def test_factory_function():
    """Test create_status_syncer factory."""
    syncer = create_status_syncer()
    assert isinstance(syncer, StatusSyncer)


# ============================================================================
# STATUS UPDATE TESTS
# ============================================================================

def test_update_status_success():
    """Test successful status update."""
    syncer = StatusSyncer()

    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Task updated",
            stderr=""
        )

        syncer._update_status("task-123", "In Progress")

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "backlog" in args
        assert "task" in args
        assert "edit" in args
        assert "task-123" in args
        assert "--status" in args
        assert "In Progress" in args


def test_update_status_failure():
    """Test status update failure."""
    syncer = StatusSyncer()

    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            returncode=1,
            stderr="Task not found"
        )

        with pytest.raises(StatusSyncerError, match="Failed to update status"):
            syncer._update_status("task-nonexistent", "Done")


# ============================================================================
# PR URL TRACKING TESTS
# ============================================================================

def test_add_pr_url_success():
    """Test adding PR URL to task notes."""
    syncer = StatusSyncer()

    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Note added",
            stderr=""
        )

        syncer._add_pr_url("task-123", "https://github.com/user/repo/pull/42")

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "backlog" in args
        assert "task" in args
        assert "edit" in args
        assert "task-123" in args
        assert "--notes-append" in args
        assert "PR: https://github.com/user/repo/pull/42" in args


def test_add_pr_url_failure():
    """Test PR URL addition failure."""
    syncer = StatusSyncer()

    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            returncode=1,
            stderr="Failed to update notes"
        )

        with pytest.raises(StatusSyncerError, match="Failed to add PR URL"):
            syncer._add_pr_url("task-123", "https://github.com/user/repo/pull/42")


# ============================================================================
# TASK.MD SYNC TESTS
# ============================================================================

def test_sync_task_md_success():
    """Test TASK.md sync."""
    syncer = StatusSyncer()

    with patch('pathlib.Path.exists', return_value=True):
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="Sync complete",
                stderr=""
            )

            syncer._sync_task_md()

            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert "poetry" in args
            assert "run" in args
            assert "python" in args


def test_sync_task_md_script_not_found():
    """Test TASK.md sync when script missing."""
    syncer = StatusSyncer()

    with patch('pathlib.Path.exists', return_value=False):
        # Should not raise, just log warning
        syncer._sync_task_md()


def test_sync_task_md_failure():
    """Test TASK.md sync failure."""
    syncer = StatusSyncer()

    with patch('pathlib.Path.exists', return_value=True):
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stderr="Sync failed"
            )

            with pytest.raises(StatusSyncerError, match="TASK.md sync failed"):
                syncer._sync_task_md()


# ============================================================================
# FULL SYNC TESTS
# ============================================================================

def test_sync_status_complete_workflow():
    """Test complete sync workflow."""
    syncer = StatusSyncer()

    with patch.object(syncer, '_update_status') as mock_update:
        with patch.object(syncer, '_add_pr_url') as mock_add_url:
            with patch.object(syncer, '_sync_task_md') as mock_sync:
                result = syncer.sync_status(
                    "task-scaffold-pr-creation",
                    "Done",
                    pr_url="https://github.com/user/repo/pull/82"
                )

                assert result is True
                mock_update.assert_called_once_with("task-scaffold-pr-creation", "Done")
                mock_add_url.assert_called_once_with(
                    "task-scaffold-pr-creation",
                    "https://github.com/user/repo/pull/82"
                )
                mock_sync.assert_called_once()


def test_sync_status_without_pr_url():
    """Test sync without PR URL."""
    syncer = StatusSyncer()

    with patch.object(syncer, '_update_status') as mock_update:
        with patch.object(syncer, '_add_pr_url') as mock_add_url:
            with patch.object(syncer, '_sync_task_md') as mock_sync:
                result = syncer.sync_status("task-123", "In Progress")

                assert result is True
                mock_update.assert_called_once()
                mock_add_url.assert_not_called()  # No PR URL provided
                mock_sync.assert_called_once()


def test_sync_status_graceful_failure():
    """Test sync failure is graceful (returns False, doesn't raise)."""
    syncer = StatusSyncer()

    with patch.object(syncer, '_update_status', side_effect=StatusSyncerError("Update failed")):
        result = syncer.sync_status("task-123", "Done")

        assert result is False  # Failed but didn't raise


# ============================================================================
# CONVENIENCE METHODS TESTS
# ============================================================================

def test_mark_in_progress():
    """Test mark_in_progress convenience method."""
    syncer = StatusSyncer()

    with patch.object(syncer, 'sync_status', return_value=True) as mock_sync:
        result = syncer.mark_in_progress("task-123")

        assert result is True
        mock_sync.assert_called_once_with("task-123", "In Progress")


def test_mark_done_with_pr():
    """Test mark_done with PR URL."""
    syncer = StatusSyncer()

    with patch.object(syncer, 'sync_status', return_value=True) as mock_sync:
        result = syncer.mark_done(
            "task-123",
            pr_url="https://github.com/user/repo/pull/42"
        )

        assert result is True
        mock_sync.assert_called_once_with(
            "task-123",
            "Done",
            pr_url="https://github.com/user/repo/pull/42"
        )


def test_mark_done_without_pr():
    """Test mark_done without PR URL."""
    syncer = StatusSyncer()

    with patch.object(syncer, 'sync_status', return_value=True) as mock_sync:
        result = syncer.mark_done("task-123")

        assert result is True
        mock_sync.assert_called_once_with("task-123", "Done", pr_url=None)


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

def test_sync_status_subprocess_timeout():
    """Test sync with subprocess timeout."""
    syncer = StatusSyncer()

    with patch.object(syncer, '_update_status', side_effect=subprocess.TimeoutExpired("backlog", 10)):
        result = syncer.sync_status("task-123", "Done")

        assert result is False


def test_sync_status_generic_exception():
    """Test sync with generic exception."""
    syncer = StatusSyncer()

    with patch.object(syncer, '_update_status', side_effect=Exception("Unknown error")):
        result = syncer.sync_status("task-123", "Done")

        assert result is False


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

def test_full_integration_workflow():
    """Test complete integration workflow."""
    syncer = StatusSyncer(repo_root=Path("/test/repo"))

    with patch('subprocess.run') as mock_run:
        # Mock all subprocess calls to succeed
        mock_run.return_value = MagicMock(returncode=0, stdout="Success", stderr="")

        with patch('pathlib.Path.exists', return_value=True):
            result = syncer.sync_status(
                "task-scaffold-backlog-sync",
                "Done",
                pr_url="https://github.com/user/repo/pull/83"
            )

            assert result is True
            # Should have called: status update, PR URL add, TASK.md sync
            assert mock_run.call_count == 3

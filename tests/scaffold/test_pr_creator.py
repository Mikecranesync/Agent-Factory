"""Tests for PRCreator - Pull Request Creation

Tests cover:
- Initialization
- Branch detection
- Commit message generation
- Git operations (commit, push)
- PR body generation
- PR creation via gh CLI
- Integration workflow
- Error handling
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import subprocess

from agent_factory.scaffold.pr_creator import (
    PRCreator,
    PRCreatorError,
    create_pr_creator
)


# ============================================================================
# INITIALIZATION TESTS
# ============================================================================

def test_init_default_values():
    """Test PRCreator initialization with defaults."""
    creator = PRCreator(repo_root=Path.cwd())

    assert creator.repo_root == Path.cwd().resolve()
    assert creator.gh_cmd == "gh"
    assert creator.default_base == "main"
    assert creator.backlog_parser is not None


def test_init_custom_values():
    """Test PRCreator initialization with custom values."""
    creator = PRCreator(
        repo_root=Path("/custom/path"),
        gh_cmd="custom-gh",
        default_base="develop"
    )

    assert creator.repo_root == Path("/custom/path").resolve()
    assert creator.gh_cmd == "custom-gh"
    assert creator.default_base == "develop"


def test_factory_function():
    """Test create_pr_creator factory function."""
    creator = create_pr_creator()
    assert isinstance(creator, PRCreator)
    assert creator.repo_root == Path.cwd().resolve()


def test_factory_with_custom_repo():
    """Test factory with custom repo root."""
    custom_root = Path("/custom/repo")
    creator = create_pr_creator(repo_root=custom_root)
    assert creator.repo_root == custom_root.resolve()


# ============================================================================
# BRANCH DETECTION TESTS
# ============================================================================

def test_get_current_branch_success():
    """Test successful branch detection."""
    creator = PRCreator(repo_root=Path.cwd())

    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="scaffold/pr-creator\n",
            stderr=""
        )

        branch = creator._get_current_branch("/path/to/worktree")

        assert branch == "scaffold/pr-creator"
        mock_run.assert_called_once()


def test_get_current_branch_failure():
    """Test branch detection failure."""
    creator = PRCreator(repo_root=Path.cwd())

    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="fatal: not a git repository"
        )

        with pytest.raises(PRCreatorError, match="Failed to get branch name"):
            creator._get_current_branch("/invalid/path")


def test_get_current_branch_detached_head():
    """Test branch detection with detached HEAD."""
    creator = PRCreator(repo_root=Path.cwd())

    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="",  # Empty = detached HEAD
            stderr=""
        )

        with pytest.raises(PRCreatorError, match="No current branch"):
            creator._get_current_branch("/path/to/worktree")


# ============================================================================
# COMMIT MESSAGE TESTS
# ============================================================================

def test_build_commit_message_build_type():
    """Test commit message generation for BUILD task."""
    creator = PRCreator(repo_root=Path.cwd())

    task = {
        "id": "task-123",
        "title": "BUILD: PR Creation Feature",
        "description": "Create draft PRs automatically"
    }

    message = creator._build_commit_message(task)

    assert message.startswith("feat: PR Creation Feature")
    assert "Create draft PRs automatically" in message
    assert "Completes: task-123" in message
    assert "Claude Code" in message


def test_build_commit_message_fix_type():
    """Test commit message generation for FIX task."""
    creator = PRCreator(repo_root=Path.cwd())

    task = {
        "id": "task-456",
        "title": "FIX: Unicode Encoding Bug",
        "description": "Fix Windows console encoding"
    }

    message = creator._build_commit_message(task)

    assert message.startswith("fix: Unicode Encoding Bug")
    assert "Fix Windows console encoding" in message
    assert "Completes: task-456" in message


def test_build_commit_message_no_type():
    """Test commit message generation without type prefix."""
    creator = PRCreator(repo_root=Path.cwd())

    task = {
        "id": "task-789",
        "title": "Improve Documentation",
        "description": "Add more examples"
    }

    message = creator._build_commit_message(task)

    # Should default to "feat"
    assert message.startswith("feat: Improve Documentation")


# ============================================================================
# GIT OPERATIONS TESTS
# ============================================================================

def test_commit_changes_success():
    """Test successful commit."""
    creator = PRCreator(repo_root=Path.cwd())

    with patch('subprocess.run') as mock_run:
        # Mock git add success
        mock_add = MagicMock(returncode=0, stdout="", stderr="")
        # Mock git commit success
        mock_commit = MagicMock(
            returncode=0,
            stdout="[main abc123] feat: Test commit\n1 file changed",
            stderr=""
        )

        mock_run.side_effect = [mock_add, mock_commit]

        # Should not raise
        creator._commit_changes("/path/to/worktree", "test commit message")

        assert mock_run.call_count == 2


def test_commit_changes_nothing_to_commit():
    """Test commit with no changes."""
    creator = PRCreator(repo_root=Path.cwd())

    with patch('subprocess.run') as mock_run:
        mock_add = MagicMock(returncode=0)
        mock_commit = MagicMock(
            returncode=1,
            stdout="nothing to commit, working tree clean",
            stderr=""
        )

        mock_run.side_effect = [mock_add, mock_commit]

        # Should not raise (nothing to commit is OK)
        creator._commit_changes("/path/to/worktree", "test message")


def test_commit_changes_add_failure():
    """Test commit when git add fails."""
    creator = PRCreator(repo_root=Path.cwd())

    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="fatal: pathspec did not match"
        )

        with pytest.raises(PRCreatorError, match="git add failed"):
            creator._commit_changes("/path/to/worktree", "test message")


def test_push_branch_success():
    """Test successful branch push."""
    creator = PRCreator(repo_root=Path.cwd())

    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Branch 'feat/test' set up to track 'origin/feat/test'",
            stderr=""
        )

        creator._push_branch("/path/to/worktree", "feat/test")

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "git" in args
        assert "push" in args
        assert "feat/test" in args


def test_push_branch_failure():
    """Test branch push failure."""
    creator = PRCreator(repo_root=Path.cwd())

    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="error: failed to push some refs"
        )

        with pytest.raises(PRCreatorError, match="git push failed"):
            creator._push_branch("/path/to/worktree", "feat/test")


# ============================================================================
# PR BODY GENERATION TESTS
# ============================================================================

def test_build_pr_title():
    """Test PR title generation."""
    creator = PRCreator(repo_root=Path.cwd())

    task = {"title": "BUILD: Amazing Feature"}
    title = creator._build_pr_title(task)

    assert title == "BUILD: Amazing Feature"


def test_build_pr_body_with_criteria():
    """Test PR body with acceptance criteria."""
    creator = PRCreator(repo_root=Path.cwd())

    task = {
        "id": "task-123",
        "description": "Add new feature",
        "acceptance_criteria": [
            "Feature works",
            "Tests pass",
            "Documentation updated"
        ]
    }

    body = creator._build_pr_body(task)

    assert "Add new feature" in body
    assert "- [ ] Feature works" in body
    assert "- [ ] Tests pass" in body
    assert "- [ ] Documentation updated" in body
    assert "task-123" in body


def test_build_pr_body_no_criteria():
    """Test PR body without acceptance criteria."""
    creator = PRCreator(repo_root=Path.cwd())

    task = {
        "id": "task-456",
        "description": "Simple fix"
    }

    body = creator._build_pr_body(task)

    assert "Simple fix" in body
    assert "None specified" in body
    assert "task-456" in body


# ============================================================================
# PR CREATION TESTS
# ============================================================================

def test_create_draft_pr_success():
    """Test successful draft PR creation."""
    creator = PRCreator(repo_root=Path.cwd())

    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="https://github.com/user/repo/pull/42\n",
            stderr=""
        )

        pr_url = creator._create_draft_pr(
            "/path/to/worktree",
            "Test PR",
            "Test body",
            "feat/test",
            "main"
        )

        assert pr_url == "https://github.com/user/repo/pull/42"
        mock_run.assert_called_once()

        args = mock_run.call_args[0][0]
        assert "gh" in args
        assert "pr" in args
        assert "create" in args
        assert "--draft" in args


def test_create_draft_pr_url_extraction():
    """Test PR URL extraction from gh output."""
    creator = PRCreator(repo_root=Path.cwd())

    with patch('subprocess.run') as mock_run:
        # gh sometimes returns formatted output
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Creating pull request for feat/test into main\nhttps://github.com/user/repo/pull/43\n",
            stderr=""
        )

        pr_url = creator._create_draft_pr(
            "/path/to/worktree",
            "Test PR",
            "Test body",
            "feat/test",
            "main"
        )

        assert pr_url == "https://github.com/user/repo/pull/43"


def test_create_draft_pr_failure():
    """Test draft PR creation failure."""
    creator = PRCreator(repo_root=Path.cwd())

    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="GraphQL: Pull request already exists"
        )

        with pytest.raises(PRCreatorError, match="gh pr create failed"):
            creator._create_draft_pr(
                "/path/to/worktree",
                "Test PR",
                "Test body",
                "feat/test",
                "main"
            )


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

def test_create_pr_full_workflow():
    """Test full PR creation workflow."""
    creator = PRCreator(repo_root=Path.cwd())

    task = {
        "id": "task-scaffold-pr-creation",
        "title": "BUILD: PR Creator",
        "description": "Automated PR creation",
        "acceptance_criteria": ["Create draft PR", "Link to task"]
    }

    with patch.object(creator.backlog_parser, 'get_task', return_value=task):
        with patch.object(creator, '_get_current_branch', return_value="scaffold/pr-creator"):
            with patch.object(creator, '_commit_changes'):
                with patch.object(creator, '_push_branch'):
                    with patch.object(creator, '_create_draft_pr', return_value="https://github.com/user/repo/pull/100"):
                        pr_url = creator.create_pr(
                            "task-scaffold-pr-creation",
                            "/path/to/worktree"
                        )

                        assert pr_url == "https://github.com/user/repo/pull/100"


def test_create_pr_task_not_found():
    """Test PR creation when task not found."""
    creator = PRCreator(repo_root=Path.cwd())

    with patch.object(creator.backlog_parser, 'get_task', return_value=None):
        with pytest.raises(PRCreatorError, match="Task not found"):
            creator.create_pr("task-nonexistent", "/path/to/worktree")


def test_create_pr_with_custom_base():
    """Test PR creation with custom base branch."""
    creator = PRCreator(repo_root=Path.cwd())

    task = {
        "id": "task-test",
        "title": "Test Task",
        "description": "Test description"
    }

    with patch.object(creator.backlog_parser, 'get_task', return_value=task):
        with patch.object(creator, '_get_current_branch', return_value="feat/test"):
            with patch.object(creator, '_commit_changes'):
                with patch.object(creator, '_push_branch'):
                    with patch.object(creator, '_create_draft_pr', return_value="https://github.com/user/repo/pull/101") as mock_create:
                        creator.create_pr(
                            "task-test",
                            "/path/to/worktree",
                            base_branch="develop"
                        )

                        # Verify custom base was used
                        args = mock_create.call_args[0]
                        assert args[4] == "develop"  # base_branch argument


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

def test_create_pr_subprocess_error():
    """Test PR creation with subprocess error."""
    creator = PRCreator(repo_root=Path.cwd())

    task = {
        "id": "task-test",
        "title": "Test",
        "description": "Test"
    }

    with patch.object(creator.backlog_parser, 'get_task', return_value=task):
        with patch.object(creator, '_get_current_branch', side_effect=subprocess.TimeoutExpired("git", 5)):
            with pytest.raises(PRCreatorError):
                creator.create_pr("task-test", "/path/to/worktree")


def test_create_pr_generic_exception():
    """Test PR creation with generic exception."""
    creator = PRCreator(repo_root=Path.cwd())

    with patch.object(creator.backlog_parser, 'get_task', side_effect=Exception("Database error")):
        with pytest.raises(PRCreatorError, match="PR creation error"):
            creator.create_pr("task-test", "/path/to/worktree")

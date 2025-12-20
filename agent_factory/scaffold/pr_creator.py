"""SCAFFOLD Platform - Pull Request Creator

Creates draft PRs automatically after task completion.

Features:
- Commits all changes in worktree with detailed message
- Pushes branch to origin
- Creates draft PR using GitHub CLI (gh)
- Links PR to task ID
- Returns PR URL

Example:
    >>> creator = PRCreator(repo_root=Path.cwd())
    >>> pr_url = creator.create_pr(task_id="task-123", worktree_path="/path/to/worktree")
    >>> print(f"Draft PR created: {pr_url}")
"""

import logging
import subprocess
from pathlib import Path
from typing import Optional
import re

from agent_factory.scaffold.backlog_parser import BacklogParser

logger = logging.getLogger(__name__)


class PRCreatorError(Exception):
    """Base exception for PRCreator errors."""
    pass


class PRCreator:
    """Create draft pull requests automatically.

    Manages the complete PR creation workflow:
    - Commits changes with conventional commit message
    - Pushes branch to origin
    - Creates draft PR via GitHub CLI
    - Links to task in PR body
    """

    def __init__(
        self,
        repo_root: Path,
        gh_cmd: str = "gh",
        default_base: str = "main"
    ):
        """Initialize PRCreator.

        Args:
            repo_root: Root directory of repository
            gh_cmd: GitHub CLI command (default: "gh")
            default_base: Default base branch for PRs (default: "main")
        """
        self.repo_root = Path(repo_root).resolve()
        self.gh_cmd = gh_cmd
        self.default_base = default_base
        self.backlog_parser = BacklogParser()

    def create_pr(
        self,
        task_id: str,
        worktree_path: str,
        base_branch: Optional[str] = None
    ) -> str:
        """Create draft PR for completed task.

        Args:
            task_id: Task identifier (e.g., "task-scaffold-pr-creation")
            worktree_path: Path to git worktree containing changes
            base_branch: Target branch for PR (default: self.default_base)

        Returns:
            PR URL (e.g., "https://github.com/user/repo/pull/42")

        Raises:
            PRCreatorError: If PR creation fails
        """
        logger.info(f"Creating PR for task {task_id} in worktree {worktree_path}")

        base_branch = base_branch or self.default_base

        try:
            # Fetch task details from Backlog.md
            task = self.backlog_parser.get_task(task_id)
            if not task:
                raise PRCreatorError(f"Task not found: {task_id}")

            # Get current branch name
            branch_name = self._get_current_branch(worktree_path)
            logger.info(f"Current branch: {branch_name}")

            # Commit changes
            commit_message = self._build_commit_message(task)
            self._commit_changes(worktree_path, commit_message)

            # Push branch
            self._push_branch(worktree_path, branch_name)

            # Create draft PR
            pr_title = self._build_pr_title(task)
            pr_body = self._build_pr_body(task)
            pr_url = self._create_draft_pr(
                worktree_path,
                pr_title,
                pr_body,
                branch_name,
                base_branch
            )

            logger.info(f"Draft PR created: {pr_url}")
            return pr_url

        except Exception as e:
            logger.error(f"PR creation failed for task {task_id}: {e}")
            raise PRCreatorError(f"PR creation error: {e}") from e

    def _get_current_branch(self, worktree_path: str) -> str:
        """Get current branch name in worktree.

        Args:
            worktree_path: Path to worktree

        Returns:
            Branch name

        Raises:
            PRCreatorError: If branch detection fails
        """
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=worktree_path,
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            raise PRCreatorError(f"Failed to get branch name: {result.stderr}")

        branch_name = result.stdout.strip()
        if not branch_name:
            raise PRCreatorError("No current branch (detached HEAD?)")

        return branch_name

    def _build_commit_message(self, task: dict) -> str:
        """Build conventional commit message from task.

        Args:
            task: Task dict with id, title, description

        Returns:
            Formatted commit message
        """
        # Extract type from task title (e.g., "BUILD: Feature" -> "feat")
        title = task.get("title", "")
        type_map = {
            "BUILD": "feat",
            "FIX": "fix",
            "TEST": "test",
            "CLEANUP": "chore",
            "AUDIT": "docs",
        }

        commit_type = "feat"  # default
        for prefix, ctype in type_map.items():
            if title.startswith(prefix):
                commit_type = ctype
                break

        # Remove type prefix from title for commit message
        clean_title = re.sub(r"^(BUILD|FIX|TEST|CLEANUP|AUDIT):\s*", "", title)

        # Build commit message
        message = f"""{commit_type}: {clean_title}

{task.get('description', 'No description provided')}

Completes: {task.get('id', 'unknown')}

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"""

        return message

    def _commit_changes(self, worktree_path: str, message: str):
        """Commit all changes in worktree.

        Args:
            worktree_path: Path to worktree
            message: Commit message

        Raises:
            PRCreatorError: If commit fails
        """
        # Stage all changes
        result = subprocess.run(
            ["git", "add", "."],
            cwd=worktree_path,
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            raise PRCreatorError(f"git add failed: {result.stderr}")

        # Commit with message
        result = subprocess.run(
            ["git", "commit", "-m", message],
            cwd=worktree_path,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            # Check if "nothing to commit" (not an error)
            if "nothing to commit" in result.stdout.lower():
                logger.warning("No changes to commit")
                return
            raise PRCreatorError(f"git commit failed: {result.stderr}")

        logger.info("Changes committed successfully")

    def _push_branch(self, worktree_path: str, branch_name: str):
        """Push branch to origin.

        Args:
            worktree_path: Path to worktree
            branch_name: Name of branch to push

        Raises:
            PRCreatorError: If push fails
        """
        result = subprocess.run(
            ["git", "push", "-u", "origin", branch_name],
            cwd=worktree_path,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            raise PRCreatorError(f"git push failed: {result.stderr}")

        logger.info(f"Branch {branch_name} pushed to origin")

    def _build_pr_title(self, task: dict) -> str:
        """Build PR title from task.

        Args:
            task: Task dict with title

        Returns:
            PR title
        """
        return task.get("title", "Untitled Task")

    def _build_pr_body(self, task: dict) -> str:
        """Build PR body with task summary and acceptance criteria.

        Args:
            task: Task dict with id, description, acceptance_criteria

        Returns:
            Formatted PR body (GitHub markdown)
        """
        criteria = task.get("acceptance_criteria", [])
        criteria_list = "\n".join(f"- [ ] {c}" for c in criteria) if criteria else "None specified"

        body = f"""## Summary

{task.get('description', 'No description provided')}

## Acceptance Criteria

{criteria_list}

## Task Reference

Completes: `{task.get('id', 'unknown')}`

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"""

        return body

    def _create_draft_pr(
        self,
        worktree_path: str,
        title: str,
        body: str,
        head_branch: str,
        base_branch: str
    ) -> str:
        """Create draft PR using GitHub CLI.

        Args:
            worktree_path: Path to worktree
            title: PR title
            body: PR body (markdown)
            head_branch: Source branch
            base_branch: Target branch

        Returns:
            PR URL

        Raises:
            PRCreatorError: If PR creation fails
        """
        # Create draft PR
        result = subprocess.run(
            [
                self.gh_cmd,
                "pr",
                "create",
                "--title", title,
                "--body", body,
                "--base", base_branch,
                "--head", head_branch,
                "--draft"
            ],
            cwd=worktree_path,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            raise PRCreatorError(f"gh pr create failed: {result.stderr}")

        # Extract PR URL from output
        pr_url = result.stdout.strip()
        if not pr_url.startswith("http"):
            # Try to parse from output (gh sometimes returns different formats)
            match = re.search(r"https://github\.com/[^\s]+/pull/\d+", result.stdout)
            if match:
                pr_url = match.group(0)
            else:
                raise PRCreatorError(f"Could not extract PR URL from: {result.stdout}")

        return pr_url


def create_pr_creator(
    repo_root: Optional[Path] = None,
    gh_cmd: str = "gh",
    default_base: str = "main"
) -> PRCreator:
    """Factory function to create PRCreator.

    Args:
        repo_root: Repository root (defaults to cwd)
        gh_cmd: GitHub CLI command
        default_base: Default base branch for PRs

    Returns:
        PRCreator instance
    """
    if repo_root is None:
        repo_root = Path.cwd()

    return PRCreator(
        repo_root=repo_root,
        gh_cmd=gh_cmd,
        default_base=default_base
    )

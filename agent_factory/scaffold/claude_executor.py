"""SCAFFOLD Platform - Claude Code CLI Executor

Executes tasks using Claude Code CLI in headless mode.

Features:
- Assembles execution context via ContextAssembler
- Invokes claude-code CLI with --non-interactive flag
- Captures output and parses results
- Returns structured ExecutionResult

Example:
    >>> executor = ClaudeExecutor(repo_root=Path.cwd())
    >>> result = executor.execute_task(task, worktree_path)
    >>> if result.success:
    ...     print(f"Task completed: {len(result.files_changed)} files changed")
"""

import logging
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional
import re

from agent_factory.scaffold.context_assembler import ContextAssembler
from agent_factory.scaffold.models import ExecutionResult

logger = logging.getLogger(__name__)


class ClaudeExecutorError(Exception):
    """Base exception for ClaudeExecutor errors."""
    pass


class ClaudeExecutor:
    """Execute tasks using Claude Code CLI.

    Manages headless Claude Code CLI execution:
    - Assembles execution context
    - Invokes claude-code with --non-interactive
    - Parses output for success indicators
    - Returns structured results
    """

    def __init__(
        self,
        repo_root: Path,
        claude_cmd: str = "claude-code",
        timeout_sec: int = 3600
    ):
        """Initialize ClaudeExecutor.

        Args:
            repo_root: Root directory of repository
            claude_cmd: Claude Code CLI command (default: "claude-code")
            timeout_sec: Maximum execution time in seconds (default: 1 hour)
        """
        self.repo_root = Path(repo_root).resolve()
        self.claude_cmd = claude_cmd
        self.timeout_sec = timeout_sec
        self.context_assembler = ContextAssembler(repo_root=repo_root)

    def execute_task(
        self,
        task: Dict,
        worktree_path: str
    ) -> ExecutionResult:
        """Execute task using Claude Code CLI.

        Args:
            task: Task dict with id, title, description, acceptance_criteria
            worktree_path: Path to git worktree for execution

        Returns:
            ExecutionResult with success status, output, files changed, etc.

        Raises:
            ClaudeExecutorError: If execution fails critically
        """
        task_id = task.get("id", "unknown")
        logger.info(f"Executing task {task_id} in worktree {worktree_path}")

        start_time = time.time()

        try:
            # Assemble execution context
            context = self.context_assembler.assemble_context(task, worktree_path)
            logger.debug(f"Context assembled: {len(context)} chars")

            # Execute Claude Code CLI
            output, exit_code = self._invoke_claude_cli(context, worktree_path)
            duration_sec = time.time() - start_time

            # Parse results
            success = self._is_successful(output, exit_code)
            files_changed = self._extract_files_changed(output, worktree_path)
            cost_usd = self._estimate_cost(output)
            error = None if success else self._extract_error(output)

            result = ExecutionResult(
                success=success,
                files_changed=files_changed,
                output=output,
                error=error,
                cost=cost_usd,
                duration_sec=duration_sec,
                commit_created=False,
                tests_passed=None
            )

            logger.info(
                f"Task {task_id} {'succeeded' if success else 'failed'} "
                f"(exit_code={exit_code}, duration={duration_sec:.1f}s, "
                f"files_changed={len(files_changed)})"
            )

            return result

        except subprocess.TimeoutExpired:
            duration_sec = time.time() - start_time
            error = f"Execution timeout after {self.timeout_sec}s"
            logger.error(f"Task {task_id}: {error}")

            return ExecutionResult(
                success=False,
                files_changed=[],
                output="",
                error=error,
                cost=0.0,
                duration_sec=duration_sec,
                commit_created=False,
                tests_passed=None
            )

        except Exception as e:
            duration_sec = time.time() - start_time
            error = f"Execution failed: {str(e)}"
            logger.exception(f"Task {task_id}: {error}")

            return ExecutionResult(
                success=False,
                files_changed=[],
                output="",
                error=error,
                cost=0.0,
                duration_sec=duration_sec,
                commit_created=False,
                tests_passed=None
            )

    def _invoke_claude_cli(
        self,
        context: str,
        worktree_path: str
    ) -> tuple[str, int]:
        """Invoke claude-code CLI with context.

        Args:
            context: Full execution context string
            worktree_path: Working directory for execution

        Returns:
            Tuple of (output, exit_code)
        """
        # Build command
        cmd = [
            self.claude_cmd,
            "--non-interactive",
            "--prompt", context
        ]

        logger.debug(f"Invoking: {' '.join(cmd[:2])} --prompt '<context>'")

        # Execute
        result = subprocess.run(
            cmd,
            cwd=worktree_path,
            capture_output=True,
            text=True,
            timeout=self.timeout_sec
        )

        # Combine stdout and stderr
        output = result.stdout
        if result.stderr:
            output += f"\n\n--- STDERR ---\n{result.stderr}"

        return output, result.returncode

    def _is_successful(self, output: str, exit_code: int) -> bool:
        """Determine if execution succeeded.

        Success indicators:
        - Exit code 0
        - "completed successfully" in output
        - Commit created (git commit found in output)
        - Tests passed

        Args:
            output: Combined stdout/stderr
            exit_code: Process exit code

        Returns:
            True if execution succeeded
        """
        if exit_code != 0:
            return False

        # Look for success indicators in output
        success_patterns = [
            r"completed successfully",
            r"all tests? passed",
            r"git commit.*created",
            r"implementation complete",
            r"task complete",
            r"\d+ files? changed"
        ]

        output_lower = output.lower()
        for pattern in success_patterns:
            if re.search(pattern, output_lower):
                return True

        # If no explicit success indicators but exit code 0, consider success
        # (Claude might complete without explicit success message)
        return True

    def _extract_files_changed(
        self,
        output: str,
        worktree_path: str
    ) -> List[str]:
        """Extract list of files changed during execution.

        Looks for:
        - git diff output
        - File paths mentioned in output
        - Actual git status in worktree

        Args:
            output: Combined stdout/stderr
            worktree_path: Path to worktree

        Returns:
            List of changed file paths (relative to worktree)
        """
        files = []

        # Try git status in worktree
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD"],
                cwd=worktree_path,
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0 and result.stdout.strip():
                files.extend(result.stdout.strip().split('\n'))

        except (subprocess.TimeoutExpired, FileNotFoundError):
            logger.warning("Could not run git diff to detect changed files")

        # Fallback: parse output for file mentions
        if not files:
            # Look for patterns like "modified: path/to/file.py"
            file_patterns = [
                r"(?:modified|created|deleted):\s+([^\s]+)",
                r"([a-zA-Z0-9_/\\.-]+\.py)",
                r"([a-zA-Z0-9_/\\.-]+\.md)"
            ]

            for pattern in file_patterns:
                matches = re.findall(pattern, output)
                files.extend(matches)

        # Deduplicate and clean
        files = list(set(f.strip() for f in files if f.strip()))

        return files[:50]  # Limit to first 50 files

    def _estimate_cost(self, output: str) -> float:
        """Estimate API cost from output.

        Looks for cost indicators in Claude Code output.
        Falls back to heuristic based on output length.

        Args:
            output: Combined stdout/stderr

        Returns:
            Estimated cost in USD
        """
        # Look for explicit cost in output (Claude Code might report this)
        cost_pattern = r"cost[:\s]+\$?([\d.]+)"
        match = re.search(cost_pattern, output.lower())
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass

        # Heuristic: $0.10 per 10K chars of output (very rough estimate)
        # Actual cost depends on model, tokens, etc.
        chars = len(output)
        estimated_cost = (chars / 10000) * 0.10

        return round(estimated_cost, 4)

    def _extract_error(self, output: str) -> str:
        """Extract error message from output.

        Args:
            output: Combined stdout/stderr

        Returns:
            Error summary (first 500 chars)
        """
        # Look for ERROR: or Exception: patterns
        error_patterns = [
            r"ERROR:\s*(.+)",
            r"Exception:\s*(.+)",
            r"Failed:\s*(.+)",
            r"Error:\s*(.+)"
        ]

        for pattern in error_patterns:
            match = re.search(pattern, output, re.IGNORECASE | re.MULTILINE)
            if match:
                error = match.group(1).strip()
                return error[:500]  # Truncate to 500 chars

        # Fallback: return last 500 chars of output
        if len(output) > 500:
            return "..." + output[-500:]
        return output


def create_claude_executor(
    repo_root: Optional[Path] = None,
    claude_cmd: str = "claude-code",
    timeout_sec: int = 3600
) -> ClaudeExecutor:
    """Factory function to create ClaudeExecutor.

    Args:
        repo_root: Repository root (defaults to cwd)
        claude_cmd: Claude Code CLI command
        timeout_sec: Execution timeout in seconds

    Returns:
        ClaudeExecutor instance
    """
    if repo_root is None:
        repo_root = Path.cwd()

    return ClaudeExecutor(
        repo_root=repo_root,
        claude_cmd=claude_cmd,
        timeout_sec=timeout_sec
    )

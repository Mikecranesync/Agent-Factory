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
            files_changed = self._extract_files_changed(output, worktree_path)
            commits = self._extract_commits(output, worktree_path)
            tests_passed = self._parse_test_results(output)
            success = self._is_successful(output, exit_code, commits, tests_passed)
            error = None if success else self._extract_error(output)

            result = ExecutionResult(
                success=success,
                files_changed=files_changed,
                output=output,
                error=error,
                exit_code=exit_code,
                commits=commits,
                tests_passed=tests_passed
            )

            logger.info(
                f"Task {task_id} {'succeeded' if success else 'failed'} "
                f"(exit_code={exit_code}, commits={len(commits)}, "
                f"files_changed={len(files_changed)}, tests_passed={tests_passed})"
            )

            return result

        except subprocess.TimeoutExpired:
            error = f"Execution timeout after {self.timeout_sec}s"
            logger.error(f"Task {task_id}: {error}")

            return ExecutionResult(
                success=False,
                files_changed=[],
                output="",
                error=error,
                exit_code=-1,
                commits=[],
                tests_passed=None
            )

        except Exception as e:
            error = f"Execution failed: {str(e)}"
            logger.exception(f"Task {task_id}: {error}")

            return ExecutionResult(
                success=False,
                files_changed=[],
                output="",
                error=error,
                exit_code=-1,
                commits=[],
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

    def _is_successful(
        self,
        output: str,
        exit_code: int,
        commits: Optional[List[str]] = None,
        tests_passed: Optional[bool] = None
    ) -> bool:
        """Determine if execution succeeded.

        Success indicators:
        - Exit code 0
        - Commit created (commits list not empty)
        - Tests passed (if tests were run)
        - Success keywords in output

        Args:
            output: Combined stdout/stderr
            exit_code: Process exit code
            commits: List of commit SHAs created
            tests_passed: Test result (True/False/None)

        Returns:
            True if execution succeeded
        """
        # Exit code must be 0
        if exit_code != 0:
            return False

        # If tests were run and failed, not successful
        if tests_passed is False:
            return False

        # Strong success indicator: commit created
        if commits and len(commits) > 0:
            return True

        # Look for success keywords in output
        success_patterns = [
            r"completed successfully",
            r"all tests? passed",
            r"implementation complete",
            r"task complete",
            r"\d+ files? changed"
        ]

        output_lower = output.lower()
        for pattern in success_patterns:
            if re.search(pattern, output_lower):
                return True

        # If exit code 0 but no other indicators, consider it successful
        # (Claude Code might complete without explicit success message)
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

    def _extract_commits(self, output: str, worktree_path: str) -> List[str]:
        """Extract git commit SHAs created during execution.

        Looks for commit SHAs in:
        1. git log output in worktree (most reliable)
        2. Output patterns mentioning commits
        3. Git commit messages in output

        Args:
            output: Combined stdout/stderr
            worktree_path: Path to worktree

        Returns:
            List of commit SHAs (abbreviated, 7 chars)
        """
        commits = []

        # Method 1: Check git log in worktree for recent commits
        try:
            # Get commits from last 5 minutes (recent execution)
            result = subprocess.run(
                ["git", "log", "--since=5 minutes ago", "--pretty=format:%h"],
                cwd=worktree_path,
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0 and result.stdout.strip():
                # Each line is a commit SHA
                commit_shas = result.stdout.strip().split('\n')
                commits.extend(commit_shas)

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.warning(f"Could not run git log to detect commits: {e}")

        # Method 2: Parse output for commit SHA patterns
        # Match 7-40 char hex strings that look like git SHAs
        sha_pattern = r'\b([0-9a-f]{7,40})\b'
        potential_shas = re.findall(sha_pattern, output.lower())

        # Filter to realistic SHAs (7-40 chars, not all same digit)
        for sha in potential_shas:
            if 7 <= len(sha) <= 40 and not all(c == sha[0] for c in sha):
                # Abbreviate to 7 chars
                commits.append(sha[:7])

        # Method 3: Look for commit message indicators
        commit_msg_patterns = [
            r'commit\s+([0-9a-f]{7,40})',
            r'created commit\s+([0-9a-f]{7,40})',
            r'\[([0-9a-f]{7,40})\]'
        ]

        for pattern in commit_msg_patterns:
            matches = re.findall(pattern, output.lower())
            for sha in matches:
                commits.append(sha[:7])

        # Deduplicate and limit
        commits = list(set(commits))[:10]

        return commits

    def _parse_test_results(self, output: str) -> Optional[bool]:
        """Parse test results from output.

        Detects pytest/unittest output and determines pass/fail status.

        Args:
            output: Combined stdout/stderr

        Returns:
            True if tests passed, False if failed, None if no tests detected
        """
        output_lower = output.lower()

        # Check if tests were run
        test_run_indicators = [
            r'pytest',
            r'running.*tests?',
            r'\d+\s+passed',  # "5 passed"
            r'\d+\s+failed',  # "1 failed"
            r'all\s+tests?\s+passed',  # "All tests passed"
            r'test\s+session',
            r'unittest',
            r'ok\s+\(\d+\s+tests?\)'
        ]

        tests_detected = any(re.search(pattern, output_lower) for pattern in test_run_indicators)

        if not tests_detected:
            return None

        # Detect failures (check before success to avoid false positives)
        failure_patterns = [
            r'\d+\s+failed',  # "1 failed", "5 failed"
            r'FAILED\s+',  # "FAILED tests/..."
            r'ERROR:',  # "ERROR: ..."
            r'test.*failed',
            r'failures?:\s*[1-9]\d*'  # "failures: 1" or more
        ]

        for pattern in failure_patterns:
            if re.search(pattern, output_lower):
                return False

        # Detect success - be more specific
        success_patterns = [
            r'all\s+tests?\s+passed',  # "All tests passed"
            r'\d+\s+passed\s+in\s+[\d.]+s',  # "5 passed in 2.5s" (pytest format)
            r'\d+\s+passed.*0\s+failed',  # "5 passed, 0 failed"
            r'ok\s+\(\d+ tests?\)',  # unittest format
            r'ran\s+\d+\s+tests?.*\nok',  # unittest multiline
        ]

        for pattern in success_patterns:
            if re.search(pattern, output_lower, re.MULTILINE):
                return True

        # Tests detected but unclear result - assume failure for safety
        return False

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

    def _estimate_cost(self, output: str) -> float:
        """Estimate API cost from Claude output.

        Looks for cost patterns in output:
        - "Cost: $0.42"
        - "API cost: $1.23"
        - "Total cost: $0.56"

        Falls back to heuristic: ~$0.01 per 1000 output chars.

        Args:
            output: Claude Code CLI stdout

        Returns:
            Estimated cost in USD

        Examples:
            >>> executor._estimate_cost("Task complete. Cost: $0.42")
            0.42
            >>> executor._estimate_cost("Output with no cost")  # 20 chars
            0.0002
        """
        import re

        # Try explicit cost patterns
        cost_patterns = [
            r"Cost:\s*\$?([\d.]+)",
            r"API cost:\s*\$?([\d.]+)",
            r"Total cost:\s*\$?([\d.]+)"
        ]

        for pattern in cost_patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                return float(match.group(1))

        # Fallback: $0.01 per 1000 chars
        return len(output) / 100000


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

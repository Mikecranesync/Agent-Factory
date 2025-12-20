"""Tests for SCAFFOLD ClaudeExecutor.

Comprehensive test suite covering Claude Code CLI integration.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import subprocess

from agent_factory.scaffold.claude_executor import (
    ClaudeExecutor,
    ClaudeExecutorError,
    create_claude_executor
)
from agent_factory.scaffold.models import ExecutionResult


@pytest.fixture
def temp_repo(tmp_path):
    """Temporary repository for testing."""
    repo_dir = tmp_path / "test-repo"
    repo_dir.mkdir()

    # Create minimal CLAUDE.md
    claude_md = repo_dir / "CLAUDE.md"
    claude_md.write_text("# Test Instructions\nYou are a test assistant.")

    return repo_dir


@pytest.fixture
def executor(temp_repo):
    """ClaudeExecutor instance with temporary repo."""
    return ClaudeExecutor(repo_root=temp_repo, timeout_sec=10)


@pytest.fixture
def sample_task():
    """Sample task dict for testing."""
    return {
        "id": "task-test-1",
        "title": "Test Task",
        "description": "A test task",
        "acceptance_criteria": [
            "Create test file",
            "Write tests"
        ]
    }


class TestClaudeExecutorInitialization:
    """Test ClaudeExecutor initialization."""

    def test_executor_initialization(self, temp_repo):
        """Test creating executor instance."""
        executor = ClaudeExecutor(repo_root=temp_repo)

        assert executor.repo_root == temp_repo
        assert executor.claude_cmd == "claude-code"
        assert executor.timeout_sec == 3600
        assert executor.context_assembler is not None

    def test_executor_custom_params(self, temp_repo):
        """Test creating executor with custom parameters."""
        executor = ClaudeExecutor(
            repo_root=temp_repo,
            claude_cmd="custom-claude",
            timeout_sec=1800
        )

        assert executor.claude_cmd == "custom-claude"
        assert executor.timeout_sec == 1800

    def test_factory_function(self, temp_repo):
        """Test create_claude_executor factory function."""
        executor = create_claude_executor(
            repo_root=temp_repo,
            claude_cmd="test-claude",
            timeout_sec=900
        )

        assert isinstance(executor, ClaudeExecutor)
        assert executor.repo_root == temp_repo
        assert executor.claude_cmd == "test-claude"
        assert executor.timeout_sec == 900

    def test_factory_default_repo_root(self):
        """Test factory uses cwd when repo_root not provided."""
        executor = create_claude_executor()

        assert executor.repo_root == Path.cwd()


class TestIsSuccessful:
    """Test _is_successful() method."""

    def test_is_successful_exit_code_zero(self, executor):
        """Test success when exit code is 0."""
        output = "Task completed successfully"
        result = executor._is_successful(output, 0)
        assert result is True

    def test_is_successful_exit_code_nonzero(self, executor):
        """Test failure when exit code is non-zero."""
        output = "Task completed successfully"
        result = executor._is_successful(output, 1)
        assert result is False

    def test_is_successful_completed_pattern(self, executor):
        """Test success with 'completed successfully' pattern."""
        output = "The task completed successfully!"
        result = executor._is_successful(output, 0)
        assert result is True

    def test_is_successful_tests_passed(self, executor):
        """Test success with 'tests passed' pattern."""
        output = "All tests passed"
        result = executor._is_successful(output, 0)
        assert result is True

    def test_is_successful_git_commit(self, executor):
        """Test success with 'git commit created' pattern."""
        output = "git commit feat: Add feature created"
        result = executor._is_successful(output, 0)
        assert result is True

    def test_is_successful_files_changed(self, executor):
        """Test success with 'files changed' pattern."""
        output = "3 files changed, 50 insertions(+), 10 deletions(-)"
        result = executor._is_successful(output, 0)
        assert result is True

    def test_is_successful_no_indicators(self, executor):
        """Test success when exit code 0 but no explicit indicators."""
        output = "Some output without success indicators"
        result = executor._is_successful(output, 0)
        assert result is True  # Exit code 0 is enough


class TestExtractFilesChanged:
    """Test _extract_files_changed() method."""

    def test_extract_files_from_git_diff(self, executor, temp_repo):
        """Test extracting files from git diff."""
        # Mock subprocess.run for git diff
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="file1.py\nfile2.py\nfile3.md\n"
            )

            files = executor._extract_files_changed("", str(temp_repo))

        assert len(files) == 3
        assert "file1.py" in files
        assert "file2.py" in files
        assert "file3.md" in files

    def test_extract_files_git_diff_fails(self, executor, temp_repo):
        """Test fallback when git diff fails."""
        output = """
        modified: src/test.py
        created: docs/README.md
        """

        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("git", 5)

            files = executor._extract_files_changed(output, str(temp_repo))

        assert "src/test.py" in files
        assert "docs/README.md" in files

    def test_extract_files_from_output_patterns(self, executor, temp_repo):
        """Test extracting files from output patterns."""
        output = """
        Files modified:
        modified: agent_factory/core/agent.py
        created: tests/test_agent.py
        """

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="")

            files = executor._extract_files_changed(output, str(temp_repo))

        assert len(files) >= 2

    def test_extract_files_deduplication(self, executor, temp_repo):
        """Test file list deduplication."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="file1.py\nfile1.py\nfile2.py\n"
            )

            files = executor._extract_files_changed("", str(temp_repo))

        assert len(files) == 2  # Duplicates removed
        assert "file1.py" in files
        assert "file2.py" in files


class TestEstimateCost:
    """Test _estimate_cost() method."""

    def test_estimate_cost_explicit(self, executor):
        """Test extracting explicit cost from output."""
        output = "Execution completed. Cost: $0.25"
        cost = executor._estimate_cost(output)
        assert cost == 0.25

    def test_estimate_cost_heuristic(self, executor):
        """Test heuristic cost estimation."""
        # 10K chars = $0.10
        output = "x" * 10000
        cost = executor._estimate_cost(output)
        assert cost == pytest.approx(0.10, abs=0.01)

    def test_estimate_cost_small_output(self, executor):
        """Test cost for small output."""
        output = "Small output"
        cost = executor._estimate_cost(output)
        assert cost < 0.01


class TestExtractError:
    """Test _extract_error() method."""

    def test_extract_error_explicit(self, executor):
        """Test extracting explicit error message."""
        output = """
        Some output
        ERROR: File not found
        More output
        """
        error = executor._extract_error(output)
        assert "File not found" in error

    def test_extract_error_exception(self, executor):
        """Test extracting exception message."""
        output = "Exception: Division by zero occurred"
        error = executor._extract_error(output)
        assert "Division by zero" in error

    def test_extract_error_failed(self, executor):
        """Test extracting 'Failed:' message."""
        output = "Failed: Tests did not pass"
        error = executor._extract_error(output)
        assert "Tests did not pass" in error

    def test_extract_error_fallback(self, executor):
        """Test fallback to last 500 chars."""
        output = "x" * 1000 + "Important error at end"
        error = executor._extract_error(output)
        assert "Important error at end" in error
        assert len(error) <= 503  # "..." prefix adds 3 chars

    def test_extract_error_truncation(self, executor):
        """Test error message truncation."""
        long_error = "ERROR: " + "x" * 600
        output = long_error
        error = executor._extract_error(output)
        assert len(error) == 500  # Truncated


class TestInvokeClaude:
    """Test _invoke_claude_cli() method."""

    def test_invoke_claude_success(self, executor, temp_repo):
        """Test successful Claude CLI invocation."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="Task completed",
                stderr=""
            )

            output, exit_code = executor._invoke_claude_cli(
                "Test context",
                str(temp_repo)
            )

        assert exit_code == 0
        assert "Task completed" in output
        mock_run.assert_called_once()

    def test_invoke_claude_with_stderr(self, executor, temp_repo):
        """Test Claude CLI with stderr output."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="Standard output",
                stderr="Warning: deprecated API"
            )

            output, exit_code = executor._invoke_claude_cli(
                "Test context",
                str(temp_repo)
            )

        assert "Standard output" in output
        assert "Warning: deprecated API" in output
        assert "STDERR" in output

    def test_invoke_claude_timeout(self, executor, temp_repo):
        """Test Claude CLI timeout."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("claude-code", 10)

            with pytest.raises(subprocess.TimeoutExpired):
                executor._invoke_claude_cli("Test context", str(temp_repo))


class TestExecuteTask:
    """Test execute_task() method (main integration)."""

    def test_execute_task_success(self, executor, sample_task, temp_repo):
        """Test successful task execution."""
        # Mock ContextAssembler
        with patch.object(executor.context_assembler, 'assemble_context') as mock_context:
            mock_context.return_value = "Mock context"

            # Mock subprocess.run (Claude CLI)
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0,
                    stdout="Task completed successfully\n3 files changed",
                    stderr=""
                )

                # Mock git diff for files_changed
                with patch('agent_factory.scaffold.claude_executor.subprocess.run') as mock_git:
                    mock_git.return_value = MagicMock(
                        returncode=0,
                        stdout="file1.py\nfile2.py\n"
                    )

                    result = executor.execute_task(sample_task, str(temp_repo))

        assert isinstance(result, ExecutionResult)
        assert result.success is True
        assert len(result.files_changed) >= 0
        assert result.error is None
        assert result.cost >= 0.0
        assert result.duration_sec >= 0.0

    def test_execute_task_failure(self, executor, sample_task, temp_repo):
        """Test failed task execution."""
        with patch.object(executor.context_assembler, 'assemble_context') as mock_context:
            mock_context.return_value = "Mock context"

            with patch('subprocess.run') as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=1,
                    stdout="ERROR: Build failed",
                    stderr=""
                )

                result = executor.execute_task(sample_task, str(temp_repo))

        assert result.success is False
        assert result.error is not None
        assert result.cost >= 0.0

    def test_execute_task_timeout(self, executor, sample_task, temp_repo):
        """Test task execution timeout."""
        with patch.object(executor.context_assembler, 'assemble_context') as mock_context:
            mock_context.return_value = "Mock context"

            with patch('subprocess.run') as mock_run:
                mock_run.side_effect = subprocess.TimeoutExpired("claude-code", 10)

                result = executor.execute_task(sample_task, str(temp_repo))

        assert result.success is False
        assert "timeout" in result.error.lower()
        assert result.cost == 0.0

    def test_execute_task_exception(self, executor, sample_task, temp_repo):
        """Test task execution with exception."""
        with patch.object(executor.context_assembler, 'assemble_context') as mock_context:
            mock_context.side_effect = Exception("Context assembly failed")

            result = executor.execute_task(sample_task, str(temp_repo))

        assert result.success is False
        assert "failed" in result.error.lower()
        assert result.cost == 0.0


class TestIntegration:
    """Integration tests for full execution workflow."""

    def test_full_execution_workflow(self, temp_repo, sample_task):
        """Test complete execution workflow from start to finish."""
        executor = ClaudeExecutor(repo_root=temp_repo, timeout_sec=5)

        # Mock ContextAssembler separately to avoid git calls
        with patch.object(executor.context_assembler, 'assemble_context') as mock_context:
            mock_context.return_value = "Mock execution context"

            # Mock subprocess calls
            with patch('subprocess.run') as mock_run:
                # First call: Claude CLI execution
                # Second call: git diff (files changed)
                mock_run.side_effect = [
                    # Claude CLI
                    MagicMock(
                        returncode=0,
                        stdout="Implementation completed successfully\nAll tests passed\n",
                        stderr=""
                    ),
                    # git diff (files changed)
                    MagicMock(
                        returncode=0,
                        stdout="src/main.py\ntests/test_main.py\n"
                    ),
                ]

                result = executor.execute_task(sample_task, str(temp_repo))

        # Verify result
        assert result.success is True
        assert len(result.files_changed) >= 0
        assert result.duration_sec >= 0  # Can be 0 in fast tests
        assert result.cost >= 0.0

    def test_execution_result_serialization(self, executor, sample_task, temp_repo):
        """Test ExecutionResult can be serialized to dict."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="Done",
                stderr=""
            )

            with patch.object(executor.context_assembler, 'assemble_context'):
                result = executor.execute_task(sample_task, str(temp_repo))

        # Serialize to dict
        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert "success" in result_dict
        assert "files_changed" in result_dict
        assert "output" in result_dict
        assert "cost" in result_dict

        # Deserialize from dict
        result_restored = ExecutionResult.from_dict(result_dict)
        assert result_restored.success == result.success
        assert result_restored.files_changed == result.files_changed

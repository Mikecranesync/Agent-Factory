"""Sandbox test for ClaudeExecutor.

Tests the complete execution flow with a real task specification.
Uses mocked subprocess to avoid actual Claude CLI calls.
"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agent_factory.scaffold.claude_executor import ClaudeExecutor
from agent_factory.scaffold.models import ExecutionResult


def test_claude_executor_sandbox():
    """Test ClaudeExecutor with realistic task."""

    print("\n" + "="*70)
    print("SANDBOX TEST: ClaudeExecutor")
    print("="*70 + "\n")

    # 1. Create test task
    test_task = {
        "id": "task-sandbox-test",
        "title": "BUILD: Add logging to user authentication",
        "description": "Add structured logging to track authentication events",
        "acceptance_criteria": [
            "Log successful logins with user ID and timestamp",
            "Log failed login attempts with reason",
            "Add request correlation IDs to all auth logs",
            "Ensure logs are JSON formatted"
        ],
        "priority": "high",
        "labels": ["security", "logging", "authentication"]
    }

    print("Task Specification:")
    print(f"  ID: {test_task['id']}")
    print(f"  Title: {test_task['title']}")
    print(f"  Acceptance Criteria: {len(test_task['acceptance_criteria'])} items")
    print()

    # 2. Initialize ClaudeExecutor
    repo_root = Path.cwd()
    executor = ClaudeExecutor(
        repo_root=repo_root,
        claude_cmd="claude-code",
        timeout_sec=60
    )

    print("ClaudeExecutor Initialized:")
    print(f"  Repo Root: {executor.repo_root}")
    print(f"  Claude Command: {executor.claude_cmd}")
    print(f"  Timeout: {executor.timeout_sec}s")
    print()

    # 3. Mock subprocess calls (avoid actual Claude CLI)
    print("Mocking Claude CLI execution...")

    # Mock the actual subprocess call and git diff
    def mock_subprocess_run(*args, **kwargs):
        """Mock subprocess.run for both Claude CLI and git diff."""
        cmd = args[0] if args else kwargs.get('cmd', [])

        # Claude CLI call
        if 'claude-code' in cmd or 'claude-code' in str(cmd):
            return MagicMock(
                returncode=0,
                stdout="""
Implementation completed successfully
All tests passed
3 files changed

Created: src/auth/logging.py
Modified: src/auth/login.py
Modified: src/auth/middleware.py

Cost: $0.15
""",
                stderr=""
            )
        # Git diff call
        elif 'git' in cmd and 'diff' in cmd:
            return MagicMock(
                returncode=0,
                stdout="""src/auth/logging.py
src/auth/login.py
src/auth/middleware.py
"""
            )
        # Default
        else:
            return MagicMock(returncode=0, stdout="", stderr="")

    with patch('agent_factory.scaffold.claude_executor.subprocess.run', side_effect=mock_subprocess_run):
        # 4. Execute task
        print("Executing task...")
        result = executor.execute_task(
            task=test_task,
            worktree_path=str(repo_root)
        )

    # 5. Verify results
    print("\n" + "-"*70)
    print("EXECUTION RESULTS:")
    print("-"*70)

    print(f"\nSuccess: {result.success}")
    print(f"Task ID: {result.task_id}")
    print(f"Exit Code: {result.exit_code}")
    print(f"Duration: {result.duration_sec:.3f}s")
    print(f"Cost: ${result.cost_usd:.2f}")

    print(f"\nFiles Changed ({len(result.files_changed)}):")
    for i, file in enumerate(result.files_changed, 1):
        print(f"  {i}. {file}")

    print(f"\nOutput Preview (first 500 chars):")
    output_preview = result.output[:500] + "..." if len(result.output) > 500 else result.output
    print(f"  {output_preview}")

    if result.error:
        print(f"\nError: {result.error}")

    # 6. Validate expectations
    print("\n" + "-"*70)
    print("VALIDATION:")
    print("-"*70 + "\n")

    checks = {
        "Task succeeded": result.success == True,
        "Exit code is 0": result.exit_code == 0,
        "Files were changed": len(result.files_changed) > 0,
        "Cost was tracked": result.cost_usd > 0,
        "Duration was measured": result.duration_sec >= 0,
        "Task ID matches": result.task_id == test_task["id"],
        "No errors": result.error is None,
        "Output captured": len(result.output) > 0
    }

    all_passed = all(checks.values())

    for check_name, passed in checks.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {check_name}")

    print("\n" + "="*70)
    if all_passed:
        print("SANDBOX TEST PASSED - ClaudeExecutor working correctly!")
    else:
        print("SANDBOX TEST FAILED - Some checks did not pass")
    print("="*70 + "\n")

    # 7. Test serialization
    print("Testing ExecutionResult serialization...")
    result_dict = result.to_dict()
    result_restored = ExecutionResult.from_dict(result_dict)

    serialization_ok = (
        result_restored.success == result.success and
        result_restored.task_id == result.task_id and
        result_restored.exit_code == result.exit_code
    )

    if serialization_ok:
        print("[PASS] Serialization/deserialization working correctly\n")
    else:
        print("[FAIL] Serialization/deserialization failed\n")

    return all_passed and serialization_ok


if __name__ == "__main__":
    try:
        success = test_claude_executor_sandbox()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] SANDBOX TEST CRASHED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

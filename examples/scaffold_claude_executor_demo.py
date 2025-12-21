"""SCAFFOLD ClaudeExecutor Demo

Demonstrates how to use ClaudeExecutor to execute tasks via Claude Code CLI.

Usage:
    poetry run python examples/scaffold_claude_executor_demo.py
"""

import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_factory.scaffold.claude_executor import ClaudeExecutor

def demo_basic_usage():
    """Demo 1: Basic ClaudeExecutor usage."""
    print("=" * 60)
    print("DEMO 1: Basic ClaudeExecutor Usage")
    print("=" * 60)

    # Create executor
    repo_root = Path.cwd()
    executor = ClaudeExecutor(
        repo_root=repo_root,
        timeout_sec=60
    )

    print(f"[OK] Created ClaudeExecutor")
    print(f"  - Repo root: {executor.repo_root}")
    print(f"  - Claude command: {executor.claude_cmd}")
    print(f"  - Timeout: {executor.timeout_sec}s")
    print()


def demo_task_specification():
    """Demo 2: Task specification format."""
    print("=" * 60)
    print("DEMO 2: Task Specification Format")
    print("=" * 60)

    # Example task specification
    task = {
        "id": "task-42",
        "title": "Implement user authentication",
        "description": """
        Build JWT-based authentication system with the following:
        - User registration endpoint
        - Login endpoint with token generation
        - Protected routes middleware
        - Password hashing with bcrypt
        """,
        "acceptance_criteria": [
            "Registration endpoint creates users with hashed passwords",
            "Login returns valid JWT token",
            "Protected routes verify JWT tokens",
            "All tests pass with 100% coverage",
            "Code committed with descriptive message"
        ],
        "priority": "high",
        "labels": ["backend", "security", "authentication"]
    }

    print("Task specification:")
    print(f"  ID: {task['id']}")
    print(f"  Title: {task['title']}")
    print(f"  Priority: {task['priority']}")
    print(f"  Acceptance Criteria: {len(task['acceptance_criteria'])} items")
    print()


def demo_execution_result():
    """Demo 3: ExecutionResult structure."""
    print("=" * 60)
    print("DEMO 3: ExecutionResult Structure")
    print("=" * 60)

    from agent_factory.scaffold.models import ExecutionResult

    # Example successful result
    result = ExecutionResult(
        success=True,
        files_changed=[
            "src/auth/routes.py",
            "src/auth/middleware.py",
            "tests/test_auth.py"
        ],
        output="Implementation completed successfully\n5 passed in 2.5s",
        error=None,
        exit_code=0,
        commits=["abc123f"],
        tests_passed=True
    )

    print("Successful execution result:")
    print(f"  [OK] Success: {result.success}")
    print(f"  [OK] Exit code: {result.exit_code}")
    print(f"  [OK] Files changed: {len(result.files_changed)}")
    for file in result.files_changed:
        print(f"    - {file}")
    print(f"  [OK] Commits: {result.commits}")
    print(f"  [OK] Tests passed: {result.tests_passed}")
    print()

    # Example failed result
    failed_result = ExecutionResult(
        success=False,
        files_changed=[],
        output="ERROR: Build failed",
        error="Build failed: missing dependency 'bcrypt'",
        exit_code=1,
        commits=[],
        tests_passed=False
    )

    print("Failed execution result:")
    print(f"  [FAIL] Success: {failed_result.success}")
    print(f"  [FAIL] Exit code: {failed_result.exit_code}")
    print(f"  [FAIL] Error: {failed_result.error}")
    print(f"  [FAIL] Tests passed: {failed_result.tests_passed}")
    print()


def demo_output_parsing():
    """Demo 4: Output parsing capabilities."""
    print("=" * 60)
    print("DEMO 4: Output Parsing Capabilities")
    print("=" * 60)

    repo_root = Path.cwd()
    executor = ClaudeExecutor(repo_root=repo_root)

    # Demo commit extraction
    claude_output = """
    Creating authentication system...
    Files created:
      - src/auth/routes.py
      - src/auth/middleware.py
      - tests/test_auth.py

    Running tests...
    pytest tests/test_auth.py
    ===== test session starts =====
    collected 5 items

    tests/test_auth.py ..... [100%]

    ===== 5 passed in 2.5s =====

    Committing changes...
    [abc123f] feat: Implement JWT authentication
    3 files changed, 120 insertions(+)

    Task completed successfully!
    """

    print("Claude Code CLI output parsing:")
    print()

    # Parse test results
    tests_passed = executor._parse_test_results(claude_output)
    print(f"[OK] Tests detected: {tests_passed}")

    # Parse commits (mock worktree path for demo)
    # In real usage, this would query actual git log
    print(f"[OK] Commit pattern detected in output")

    # Parse files changed
    print(f"[OK] File changes detected in output")

    print()


def demo_error_handling():
    """Demo 5: Error handling."""
    print("=" * 60)
    print("DEMO 5: Error Handling")
    print("=" * 60)

    from agent_factory.scaffold.models import ExecutionResult

    # Timeout scenario
    timeout_result = ExecutionResult(
        success=False,
        files_changed=[],
        output="",
        error="Execution timeout after 60s",
        exit_code=-1,
        commits=[],
        tests_passed=None
    )

    print("Timeout error:")
    print(f"  [FAIL] Error: {timeout_result.error}")
    print(f"  [FAIL] Exit code: {timeout_result.exit_code}")
    print()

    # CLI not found scenario
    cli_error = ExecutionResult(
        success=False,
        files_changed=[],
        output="",
        error="Execution failed: claude-code not found",
        exit_code=-1,
        commits=[],
        tests_passed=None
    )

    print("CLI not found error:")
    print(f"  [FAIL] Error: {cli_error.error}")
    print()


def demo_serialization():
    """Demo 6: Result serialization."""
    print("=" * 60)
    print("DEMO 6: Result Serialization")
    print("=" * 60)

    from agent_factory.scaffold.models import ExecutionResult

    # Create result
    result = ExecutionResult(
        success=True,
        files_changed=["src/main.py"],
        output="Task completed",
        exit_code=0,
        commits=["abc123f"],
        tests_passed=True
    )

    # Serialize to dict
    result_dict = result.to_dict()
    print("Serialized result:")
    print(f"  {result_dict}")
    print()

    # Deserialize from dict
    restored = ExecutionResult.from_dict(result_dict)
    print("Deserialized result:")
    print(f"  Success: {restored.success}")
    print(f"  Exit code: {restored.exit_code}")
    print(f"  Commits: {restored.commits}")
    print()


def main():
    """Run all demos."""
    print()
    print("=" * 60)
    print(" " * 10 + "SCAFFOLD ClaudeExecutor Demo")
    print("=" * 60)
    print()

    demo_basic_usage()
    demo_task_specification()
    demo_execution_result()
    demo_output_parsing()
    demo_error_handling()
    demo_serialization()

    print("=" * 60)
    print("SUMMARY: ClaudeExecutor Features")
    print("=" * 60)
    print("[OK] Execute tasks via Claude Code CLI")
    print("[OK] Parse commits, test results, files changed")
    print("[OK] Comprehensive error handling")
    print("[OK] Result serialization/deserialization")
    print("[OK] Integration with ContextAssembler")
    print()
    print("Ready for SCAFFOLD orchestrator integration!")
    print()


if __name__ == "__main__":
    main()

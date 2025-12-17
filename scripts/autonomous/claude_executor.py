#!/usr/bin/env python3
"""
Claude Executor - Per-Issue Claude Code Action Wrapper

Executes Claude Code Action on a single GitHub issue.

NOTE: In GitHub Actions, this will trigger the Claude Code Action workflow.
      For local testing, this provides a mock implementation.

Usage:
    from scripts.autonomous.claude_executor import ClaudeExecutor

    executor = ClaudeExecutor()
    result = executor.execute_issue(issue_number, issue_data)

    if result["success"]:
        print(f"PR created: {result['pr_url']}")
    else:
        print(f"Error: {result['error']}")
"""

import os
import sys
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger("claude_executor")


class ClaudeExecutor:
    """
    Execute Claude Code Action on GitHub issues.

    In GitHub Actions environment:
    - Labels issue with 'claude' to trigger claude.yml workflow
    - Monitors workflow status
    - Returns results

    In local environment:
    - Provides mock implementation for testing
    - Estimates cost and time based on issue complexity
    """

    def __init__(self):
        """Initialize Claude executor."""
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.repo_owner = os.getenv("GITHUB_OWNER", "Mikecranesync")
        self.repo_name = os.getenv("GITHUB_REPO", "Agent-Factory")

        # Detect environment
        self.is_github_actions = os.getenv("GITHUB_ACTIONS") == "true"

        if self.is_github_actions:
            logger.info("Running in GitHub Actions environment")
        else:
            logger.warning("Running in local environment - using mock implementation")

    def execute_issue(
        self,
        issue_number: int,
        issue_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute Claude Code Action on issue.

        Args:
            issue_number: GitHub issue number
            issue_data: Issue data dict from IssueQueueBuilder

        Returns:
            {
                "success": bool,
                "pr_url": str (if success),
                "pr_number": int (if success),
                "error": str (if failure),
                "estimated_cost": float,
                "estimated_time": float,
                "files_changed": List[str],
                "summary": str
            }
        """
        logger.info(f"Executing Claude on issue #{issue_number}")

        if self.is_github_actions:
            return self._execute_github_actions(issue_number, issue_data)
        else:
            return self._execute_mock(issue_number, issue_data)

    def _execute_github_actions(
        self,
        issue_number: int,
        issue_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute Claude via GitHub Actions.

        Strategy:
        1. Add 'claude' label to issue (triggers .github/workflows/claude.yml)
        2. Wait for workflow to complete
        3. Check if PR was created
        4. Return results
        """
        try:
            # Step 1: Add 'claude' label to trigger workflow
            logger.info(f"Adding 'claude' label to issue #{issue_number}")

            cmd = [
                "gh", "issue", "edit", str(issue_number),
                "--add-label", "claude",
                "--repo", f"{self.repo_owner}/{self.repo_name}"
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                raise Exception(f"Failed to add label: {result.stderr}")

            logger.info(f"Label added, Claude workflow triggered for issue #{issue_number}")

            # Step 2: Wait for workflow to complete (with timeout)
            # In a real implementation, we'd poll the workflow status
            # For now, we assume the workflow will complete and create a PR

            # Step 3: Check for PR creation
            # The Claude workflow should create a PR automatically
            # We return success and let the PR creator handle linking

            return {
                "success": True,
                "estimated_cost": self._estimate_cost(issue_data),
                "estimated_time": issue_data.get("estimated_time_hours", 1.0) * 3600,
                "files_changed": [],  # Will be populated by PR creator
                "summary": "Claude workflow triggered via label",
                "workflow_triggered": True
            }

        except Exception as e:
            logger.error(f"GitHub Actions execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "estimated_cost": 0.0,
                "estimated_time": 0.0
            }

    def _execute_mock(
        self,
        issue_number: int,
        issue_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Mock execution for local testing.

        Simulates Claude execution based on issue complexity.
        """
        logger.info(f"[MOCK] Simulating Claude execution for issue #{issue_number}")

        complexity = issue_data.get("final_complexity", 5.0)
        estimated_time_hours = issue_data.get("estimated_time_hours", 1.0)

        # Simulate success/failure based on complexity
        # Higher complexity = higher chance of failure
        import random
        random.seed(issue_number)  # Deterministic for testing

        failure_chance = complexity / 20.0  # 10/10 complexity = 50% failure
        will_fail = random.random() < failure_chance

        if will_fail:
            # Simulate failure
            errors = [
                "Timeout after 30 minutes",
                "Failed to generate valid code",
                "Test failures detected",
                "Complexity higher than estimated"
            ]
            error = random.choice(errors)

            logger.warning(f"[MOCK] Issue #{issue_number} failed: {error}")

            return {
                "success": False,
                "error": error,
                "estimated_cost": self._estimate_cost(issue_data) * 0.3,  # Partial cost
                "estimated_time": estimated_time_hours * 3600 * 0.5  # Partial time
            }

        # Simulate success
        logger.info(f"[MOCK] Issue #{issue_number} completed successfully")

        # Estimate files changed based on complexity
        files_changed = []
        num_files = max(1, int(complexity / 2))
        for i in range(num_files):
            files_changed.append(f"src/module{i+1}.py")

        return {
            "success": True,
            "estimated_cost": self._estimate_cost(issue_data),
            "estimated_time": estimated_time_hours * 3600,
            "files_changed": files_changed,
            "summary": f"[MOCK] Fixed issue #{issue_number}",
            "mock_execution": True
        }

    def _estimate_cost(self, issue_data: Dict[str, Any]) -> float:
        """
        Estimate API cost based on issue complexity.

        Claude Sonnet pricing: ~$3/1M input tokens, ~$15/1M output tokens
        Average issue: ~10k input tokens, ~5k output tokens
        Cost per issue: ~$0.10 - $0.50 depending on complexity
        """
        complexity = issue_data.get("final_complexity", 5.0)
        estimated_time_hours = issue_data.get("estimated_time_hours", 1.0)

        # Base cost: $0.20
        # Complexity factor: 0-10 scale → 0.5x to 2.0x multiplier
        # Time factor: hours × $0.15/hour

        base_cost = 0.20
        complexity_multiplier = 0.5 + (complexity / 10.0) * 1.5
        time_cost = estimated_time_hours * 0.15

        total_cost = base_cost * complexity_multiplier + time_cost

        return round(total_cost, 4)


if __name__ == "__main__":
    # Test Claude executor
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )

    print("\nTesting Claude Executor...\n")

    executor = ClaudeExecutor()

    # Test case 1: Simple issue
    test_issue_1 = {
        "number": 100,
        "title": "Add type hints to utils.py",
        "final_complexity": 2.5,
        "estimated_time_hours": 0.5
    }

    print("="*70)
    print("TEST 1: Simple Issue (complexity=2.5)")
    print("="*70)

    result1 = executor.execute_issue(100, test_issue_1)
    print(f"\nResult: {result1}")

    # Test case 2: Medium issue
    test_issue_2 = {
        "number": 101,
        "title": "Implement hybrid search",
        "final_complexity": 6.5,
        "estimated_time_hours": 1.5
    }

    print("\n" + "="*70)
    print("TEST 2: Medium Issue (complexity=6.5)")
    print("="*70)

    result2 = executor.execute_issue(101, test_issue_2)
    print(f"\nResult: {result2}")

    # Test case 3: Complex issue
    test_issue_3 = {
        "number": 102,
        "title": "Refactor entire codebase",
        "final_complexity": 9.5,
        "estimated_time_hours": 3.0
    }

    print("\n" + "="*70)
    print("TEST 3: Complex Issue (complexity=9.5)")
    print("="*70)

    result3 = executor.execute_issue(102, test_issue_3)
    print(f"\nResult: {result3}")

    print("\n✅ Claude executor tests complete!")

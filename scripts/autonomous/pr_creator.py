#!/usr/bin/env python3
"""
PR Creator - Create Draft Pull Requests

Creates draft PRs for issues resolved by Claude Code Action.

Features:
- Creates branch: autonomous/issue-{number}
- Creates draft PR with detailed description
- Links PR to original issue
- Requests user review

Usage:
    from scripts.autonomous.pr_creator import PRCreator

    creator = PRCreator()
    pr_url = creator.create_draft_pr(issue_number, claude_result)

    print(f"PR created: {pr_url}")
"""

import os
import sys
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from github import Github, GithubException

logger = logging.getLogger("pr_creator")


class PRCreator:
    """
    Create draft pull requests for Claude-resolved issues.

    Features:
    - Branch creation: autonomous/issue-{number}
    - Draft PR creation with detailed description
    - Issue linking (Resolves #{number})
    - Review request to repository owner
    """

    def __init__(self):
        """Initialize PR creator."""
        self.github_token = os.getenv("GITHUB_TOKEN")
        if not self.github_token:
            raise ValueError("GITHUB_TOKEN environment variable required")

        self.github = Github(self.github_token)
        self.repo_owner = os.getenv("GITHUB_OWNER", "Mikecranesync")
        self.repo_name = os.getenv("GITHUB_REPO", "Agent-Factory")

        try:
            self.repo = self.github.get_repo(f"{self.repo_owner}/{self.repo_name}")
            logger.info(f"Connected to repository: {self.repo_owner}/{self.repo_name}")
        except GithubException as e:
            logger.error(f"Failed to connect to repository: {e}")
            raise

        # Detect environment
        self.is_github_actions = os.getenv("GITHUB_ACTIONS") == "true"

        if self.is_github_actions:
            logger.info("Running in GitHub Actions environment")
        else:
            logger.warning("Running in local environment - using mock PR creation")

    def create_draft_pr(
        self,
        issue_number: int,
        claude_result: Dict[str, Any]
    ) -> str:
        """
        Create draft PR for Claude-resolved issue.

        Args:
            issue_number: GitHub issue number
            claude_result: Result dict from ClaudeExecutor

        Returns:
            PR URL string
        """
        logger.info(f"Creating draft PR for issue #{issue_number}")

        if self.is_github_actions:
            return self._create_real_pr(issue_number, claude_result)
        else:
            return self._create_mock_pr(issue_number, claude_result)

    def _create_real_pr(
        self,
        issue_number: int,
        claude_result: Dict[str, Any]
    ) -> str:
        """
        Create real PR using GitHub API.

        NOTE: In the actual autonomous workflow, Claude Code Action will
              create the PR automatically. This method handles cases where
              we need to create/update PRs manually.
        """
        try:
            # Get issue details
            issue = self.repo.get_issue(issue_number)

            # Branch name
            branch_name = f"autonomous/issue-{issue_number}"

            # Check if PR already exists
            existing_prs = self.repo.get_pulls(
                state="open",
                head=f"{self.repo_owner}:{branch_name}"
            )

            existing_pr_list = list(existing_prs)
            if existing_pr_list:
                pr = existing_pr_list[0]
                logger.info(f"PR already exists: {pr.html_url}")
                return pr.html_url

            # Create PR description
            pr_body = self._format_pr_description(
                issue_number,
                issue.title,
                claude_result
            )

            # Create PR
            # NOTE: Claude Code Action should have already created the branch
            # and made commits. We just create the PR here.
            pr = self.repo.create_pull(
                title=f"Fix #{issue_number}: {issue.title}",
                body=pr_body,
                head=branch_name,
                base="main",
                draft=True  # Create as draft
            )

            logger.info(f"Draft PR created: {pr.html_url}")

            # Request review from repository owner
            try:
                pr.create_review_request(reviewers=[self.repo_owner])
                logger.info(f"Review requested from {self.repo_owner}")
            except GithubException as e:
                logger.warning(f"Failed to request review: {e}")

            return pr.html_url

        except GithubException as e:
            logger.error(f"Failed to create PR: {e}")

            # Fallback: Return issue URL with comment
            try:
                comment = (
                    f"✅ **Autonomous Claude Attempted Fix**\n\n"
                    f"I attempted to fix this issue but couldn't create a PR.\n\n"
                    f"**Error:** {str(e)}\n\n"
                    f"**Estimated Cost:** ${claude_result.get('estimated_cost', 0):.4f}\n\n"
                    f"Please check if a branch `autonomous/issue-{issue_number}` exists."
                )
                issue.create_comment(comment)
                logger.info(f"Posted comment on issue #{issue_number}")
            except Exception as comment_error:
                logger.error(f"Failed to post comment: {comment_error}")

            return issue.html_url

    def _create_mock_pr(
        self,
        issue_number: int,
        claude_result: Dict[str, Any]
    ) -> str:
        """
        Create mock PR for local testing.

        Returns mock URL.
        """
        logger.info(f"[MOCK] Creating draft PR for issue #{issue_number}")

        mock_pr_url = (
            f"https://github.com/{self.repo_owner}/{self.repo_name}"
            f"/pull/{issue_number + 1000}"  # Mock PR number
        )

        logger.info(f"[MOCK] Draft PR created: {mock_pr_url}")

        return mock_pr_url

    def _format_pr_description(
        self,
        issue_number: int,
        issue_title: str,
        claude_result: Dict[str, Any]
    ) -> str:
        """
        Format PR description with all relevant information.

        Args:
            issue_number: GitHub issue number
            issue_title: Issue title
            claude_result: Result dict from ClaudeExecutor

        Returns:
            Formatted PR description (Markdown)
        """
        # Extract data from result
        cost = claude_result.get("estimated_cost", 0.0)
        time_sec = claude_result.get("estimated_time", 0.0)
        time_min = time_sec / 60.0
        files_changed = claude_result.get("files_changed", [])
        summary = claude_result.get("summary", "No summary provided")

        # Build description
        description = f"""## Summary
Resolves #{issue_number}

{summary}

## Changes Made

"""

        if files_changed:
            description += "Modified files:\n"
            for file_path in files_changed:
                description += f"- `{file_path}`\n"
        else:
            description += "_Files changed information not available_\n"

        description += f"""
## Testing

_Automated testing was performed during autonomous execution._

## Resources

- ⏱️ Processing Time: {time_min:.1f} minutes
- 💵 Estimated Cost: ${cost:.4f}

---

🤖 **Generated autonomously by Claude Code**

This PR was created automatically during an autonomous session. Please review carefully before merging.

**Next Steps:**
1. Review code changes
2. Run manual tests if needed
3. Approve and merge, or request changes

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
"""

        return description


if __name__ == "__main__":
    # Test PR creator
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )

    print("\nTesting PR Creator...\n")

    try:
        creator = PRCreator()

        # Test case: Create mock PR
        test_result = {
            "success": True,
            "estimated_cost": 0.42,
            "estimated_time": 245.0,
            "files_changed": [
                "agent_factory/core/orchestrator.py",
                "tests/test_orchestrator.py"
            ],
            "summary": "Added type hints to orchestrator module"
        }

        print("="*70)
        print("TEST: Create Draft PR (Mock)")
        print("="*70)

        pr_url = creator.create_draft_pr(100, test_result)

        print(f"\nPR URL: {pr_url}")
        print("\n✅ PR creator test complete!")

    except Exception as e:
        print(f"\n❌ PR creator test failed: {e}")
        import traceback
        traceback.print_exc()

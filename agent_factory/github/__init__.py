"""
GitHub Integration for Agent Factory

This module provides GitHub integration for creating agents from issues:
- GitHubIssueParser: Parse issues to extract agent configurations
- GitHubAgentClient: Interact with GitHub API
- GitHubAgentRunner: Execute agents in GitHub Actions environment

Usage:
    from agent_factory.github import GitHubIssueParser, GitHubAgentClient

    parser = GitHubIssueParser()
    config = parser.parse_issue_url("https://github.com/user/repo/issues/42")

    client = GitHubAgentClient(token="ghp_...")
    client.create_comment(issue, "Agent created!")
"""

from .issue_parser import GitHubIssueParser
from .github_client import GitHubAgentClient

__all__ = [
    "GitHubIssueParser",
    "GitHubAgentClient",
]

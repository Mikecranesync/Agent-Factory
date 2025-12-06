"""
GitHub Agent Client - Interact with GitHub API

Provides interface to GitHub API for agent operations:
- Fetch issues and comments
- Create comments and labels
- Commit agent configs to repository
- Trigger GitHub Actions workflows

Usage:
    client = GitHubAgentClient(token="ghp_...")
    issue = client.get_issue("owner", "repo", 42)
    client.create_comment(issue, "Agent created!")
"""

import json
import os
from pathlib import Path
from typing import Optional, List, Dict, Any

try:
    from github import Github, GithubException
    from github.Issue import Issue
    from github.Repository import Repository
except ImportError:
    raise ImportError(
        "PyGithub not installed. Install with: poetry add pygithub"
    )


class GitHubAgentClient:
    """Client for interacting with GitHub API for agent operations."""

    def __init__(self, token: Optional[str] = None):
        """
        Initialize GitHub client.

        Args:
            token: GitHub personal access token (or set GITHUB_TOKEN env var)
        """
        self.token = token or os.getenv("GITHUB_TOKEN")

        if not self.token:
            raise ValueError(
                "GitHub token required. Set GITHUB_TOKEN env var or pass token parameter."
            )

        self.github = Github(self.token)
        self.user = self.github.get_user()

    def test_connection(self) -> bool:
        """
        Test GitHub API connection.

        Returns:
            True if connection successful
        """
        try:
            _ = self.user.login
            return True
        except GithubException as e:
            print(f"GitHub API connection failed: {e}")
            return False

    def get_issue(self, owner: str, repo: str, number: int) -> Issue:
        """
        Fetch GitHub issue by number.

        Args:
            owner: Repository owner
            repo: Repository name
            number: Issue number

        Returns:
            GitHub Issue object

        Raises:
            GithubException: If issue not found
        """
        repository = self.github.get_repo(f"{owner}/{repo}")
        return repository.get_issue(number)

    def get_issue_from_url(self, url: str) -> Issue:
        """
        Fetch GitHub issue from URL.

        Args:
            url: GitHub issue URL (e.g., https://github.com/user/repo/issues/42)

        Returns:
            GitHub Issue object
        """
        # Parse URL to extract owner, repo, number
        parts = url.rstrip("/").split("/")

        if "github.com" not in url or "issues" not in parts:
            raise ValueError(f"Invalid GitHub issue URL: {url}")

        # Find 'issues' index and extract parts
        issues_idx = parts.index("issues")
        owner = parts[issues_idx - 2]
        repo = parts[issues_idx - 1]
        number = int(parts[issues_idx + 1])

        return self.get_issue(owner, repo, number)

    def create_comment(self, issue: Issue, message: str) -> None:
        """
        Post comment on GitHub issue.

        Args:
            issue: GitHub Issue object
            message: Comment message (supports Markdown)
        """
        issue.create_comment(message)

    def add_labels(self, issue: Issue, labels: List[str]) -> None:
        """
        Add labels to GitHub issue.

        Args:
            issue: GitHub Issue object
            labels: List of label names to add
        """
        issue.add_to_labels(*labels)

    def remove_labels(self, issue: Issue, labels: List[str]) -> None:
        """
        Remove labels from GitHub issue.

        Args:
            issue: GitHub Issue object
            labels: List of label names to remove
        """
        for label in labels:
            try:
                issue.remove_from_labels(label)
            except GithubException:
                pass  # Label not present

    def create_agent_config_file(
        self,
        repository: Repository,
        agent_config: Dict[str, Any],
        branch: str = "main",
        path_prefix: str = ".agent_factory/agents"
    ) -> Optional[str]:
        """
        Commit agent config file to repository.

        Args:
            repository: GitHub Repository object
            agent_config: Agent configuration dictionary
            branch: Target branch (default: main)
            path_prefix: Directory path for agent configs

        Returns:
            Commit SHA if successful, None otherwise
        """
        # Generate file path
        agent_name = agent_config.get("name", "custom_agent")
        file_path = f"{path_prefix}/{agent_name}.json"

        # Convert config to JSON
        config_json = json.dumps(agent_config, indent=2)

        # Commit file
        try:
            # Check if file exists (update) or create new
            try:
                contents = repository.get_contents(file_path, ref=branch)
                commit = repository.update_file(
                    file_path,
                    f"Update agent: {agent_name}",
                    config_json,
                    contents.sha,
                    branch=branch
                )
            except GithubException:
                # File doesn't exist, create it
                commit = repository.create_file(
                    file_path,
                    f"Create agent: {agent_name}",
                    config_json,
                    branch=branch
                )

            return commit["commit"].sha

        except GithubException as e:
            print(f"Failed to commit agent config: {e}")
            return None

    def get_agent_config(
        self,
        repository: Repository,
        agent_name: str,
        branch: str = "main",
        path_prefix: str = ".agent_factory/agents"
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch agent config from repository.

        Args:
            repository: GitHub Repository object
            agent_name: Agent name
            branch: Source branch
            path_prefix: Directory path for agent configs

        Returns:
            Agent configuration dictionary, or None if not found
        """
        file_path = f"{path_prefix}/{agent_name}.json"

        try:
            contents = repository.get_contents(file_path, ref=branch)
            config_json = contents.decoded_content.decode("utf-8")
            return json.loads(config_json)
        except GithubException:
            return None

    def list_agent_configs(
        self,
        repository: Repository,
        branch: str = "main",
        path_prefix: str = ".agent_factory/agents"
    ) -> List[Dict[str, Any]]:
        """
        List all agent configs in repository.

        Args:
            repository: GitHub Repository object
            branch: Source branch
            path_prefix: Directory path for agent configs

        Returns:
            List of agent configuration dictionaries
        """
        configs = []

        try:
            contents = repository.get_contents(path_prefix, ref=branch)

            for content in contents:
                if content.name.endswith(".json"):
                    config_json = content.decoded_content.decode("utf-8")
                    config = json.loads(config_json)
                    configs.append(config)

        except GithubException as e:
            print(f"No agent configs found: {e}")

        return configs

    def trigger_workflow(
        self,
        repository: Repository,
        workflow_file: str,
        ref: str = "main",
        inputs: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Manually trigger GitHub Actions workflow.

        Args:
            repository: GitHub Repository object
            workflow_file: Workflow filename (e.g., "claude-agent.yml")
            ref: Branch or tag to run workflow on
            inputs: Workflow input parameters

        Returns:
            True if triggered successfully
        """
        try:
            workflow = repository.get_workflow(workflow_file)
            result = workflow.create_dispatch(ref=ref, inputs=inputs or {})
            return result
        except GithubException as e:
            print(f"Failed to trigger workflow: {e}")
            return False

    def check_user_permissions(self, repository: Repository) -> Dict[str, bool]:
        """
        Check user's permissions on repository.

        Args:
            repository: GitHub Repository object

        Returns:
            Dictionary with permission flags
        """
        try:
            permissions = repository.get_collaborator_permission(self.user.login)
            return {
                "can_write": permissions in ["write", "admin"],
                "can_admin": permissions == "admin",
                "permission": permissions
            }
        except GithubException:
            return {
                "can_write": False,
                "can_admin": False,
                "permission": "none"
            }

    def format_agent_created_comment(self, agent_config: Dict[str, Any], config_path: Optional[str] = None) -> str:
        """
        Format success comment for agent creation.

        Args:
            agent_config: Agent configuration
            config_path: Optional path to config file in repo

        Returns:
            Formatted Markdown comment
        """
        agent_name = agent_config.get("name", "unknown")
        role = agent_config.get("role", "AI Assistant")
        tools = ", ".join(agent_config.get("tool_collections", []))
        llm = f"{agent_config.get('llm_provider')}/{agent_config.get('model')}"

        comment = f"""## [SUCCESS] Agent Created: `{agent_name}`

**Role:** {role}
**Tools:** {tools}
**LLM:** {llm}

### Usage

**Local CLI:**
```bash
# Download agent config
agentcli github-sync

# Use agent
agentcli chat --agent {agent_name}
```

**GitHub Actions:**
Comment with `@claude run` to execute this agent.
"""

        if config_path:
            comment += f"\n**Config File:** `{config_path}`"

        comment += "\n\n*Agent created by Agent Factory*"

        return comment

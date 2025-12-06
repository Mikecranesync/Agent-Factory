"""
Tests for GitHub Integration

Tests GitHubIssueParser and GitHubAgentClient functionality.
"""

import pytest
from textwrap import dedent
from unittest.mock import Mock, patch, MagicMock
from agent_factory.github import GitHubIssueParser, GitHubAgentClient


class TestGitHubIssueParser:
    """Tests for GitHubIssueParser class."""

    def test_parser_initialization(self):
        """Test parser can be initialized."""
        parser = GitHubIssueParser()
        assert parser is not None
        assert parser.llm is None

    def test_parse_template_format_detection(self):
        """Test detection of template format."""
        parser = GitHubIssueParser()

        template_body = dedent("""
        ### Agent Name
        research_agent

        ### Role
        A research assistant

        ### Tools
        - [x] Research
        """)

        freeform_body = "Create an agent that does research"

        assert parser._is_template_format(template_body) is True
        assert parser._is_template_format(freeform_body) is False

    def test_parse_template_agent_name(self):
        """Test extracting agent name from template."""
        parser = GitHubIssueParser()

        body = dedent("""
        ### Agent Name
        my_custom_agent

        ### Role
        A helpful assistant
        """)

        config = parser.parse_issue_body(body)
        assert config["name"] == "my_custom_agent"

    def test_parse_template_role(self):
        """Test extracting role from template."""
        parser = GitHubIssueParser()

        body = dedent("""
        ### Role
        A specialized research assistant for AI topics

        ### Agent Name
        research_bot
        """)

        config = parser.parse_issue_body(body)
        assert "research assistant" in config["role"].lower()

    def test_parse_template_tools_checkboxes(self):
        """Test extracting tools from checkboxes."""
        parser = GitHubIssueParser()

        body = dedent("""
        ### Tool Collections
        - [x] Research
        - [ ] Coding
        - [x] File Operations
        - [x] Twin
        """)

        config = parser.parse_issue_body(body)
        assert "research" in config["tool_collections"]
        assert "file" in config["tool_collections"]
        assert "twin" in config["tool_collections"]
        assert "coding" not in config["tool_collections"]

    def test_parse_template_llm_provider(self):
        """Test extracting LLM provider."""
        parser = GitHubIssueParser()

        body = dedent("""
        ### LLM Provider
        Anthropic Claude

        ### Agent Name
        test_agent
        """)

        config = parser.parse_issue_body(body)
        assert config["llm_provider"] == "anthropic"

    def test_parse_template_temperature(self):
        """Test extracting temperature value."""
        parser = GitHubIssueParser()

        body = dedent("""
        ### Temperature
        0.3

        ### Agent Name
        test_agent
        """)

        config = parser.parse_issue_body(body)
        assert config["temperature"] == 0.3

    def test_parse_template_system_prompt(self):
        """Test extracting system prompt."""
        parser = GitHubIssueParser()

        body = dedent("""
        ### System Prompt
        You are a helpful research assistant specialized in AI topics.
        Always cite your sources.

        ### Agent Name
        test_agent
        """)

        config = parser.parse_issue_body(body)
        assert "research assistant" in config["system_prompt"]
        assert "cite your sources" in config["system_prompt"]

    def test_parse_template_memory_enabled(self):
        """Test extracting memory setting."""
        parser = GitHubIssueParser()

        body_enabled = dedent("""
        ### Memory
        - [x] Enable memory
        """)

        body_disabled = dedent("""
        ### Memory
        No
        """)

        config_enabled = parser.parse_issue_body(body_enabled)
        config_disabled = parser.parse_issue_body(body_disabled)

        assert config_enabled["memory_enabled"] is True
        assert config_disabled["memory_enabled"] is False

    def test_parse_freeform_agent_name(self):
        """Test extracting agent name from freeform text."""
        parser = GitHubIssueParser()

        body = """
Agent name: code_helper

I need an agent that helps with coding tasks.
        """

        config = parser.parse_issue_body(body)
        assert config["name"] == "code_helper"

    def test_parse_freeform_infer_tools(self):
        """Test inferring tools from keywords."""
        parser = GitHubIssueParser()

        body = """
I need an agent that can search the web and do research on AI topics.
It should also analyze my codebase using the project twin.
        """

        config = parser.parse_issue_body(body)
        assert "research" in config["tool_collections"]
        assert "twin" in config["tool_collections"]

    def test_parse_freeform_infer_provider(self):
        """Test inferring LLM provider from text."""
        parser = GitHubIssueParser()

        body = """
Create an agent using Claude that helps with research.
        """

        config = parser.parse_issue_body(body)
        assert config["llm_provider"] == "anthropic"

    def test_apply_defaults(self):
        """Test default values are applied."""
        parser = GitHubIssueParser()

        config = parser._apply_defaults({"role": "Test Agent"})

        assert "name" in config
        assert "tool_collections" in config
        assert "llm_provider" in config
        assert "model" in config
        assert "temperature" in config
        assert "system_prompt" in config
        assert config["agent_type"] == "react"

    def test_get_default_model_openai(self):
        """Test default OpenAI model."""
        parser = GitHubIssueParser()
        assert parser._get_default_model("openai") == "gpt-4o-mini"

    def test_get_default_model_anthropic(self):
        """Test default Anthropic model."""
        parser = GitHubIssueParser()
        assert parser._get_default_model("anthropic") == "claude-3-5-sonnet-20241022"

    def test_get_default_model_google(self):
        """Test default Google model."""
        parser = GitHubIssueParser()
        assert parser._get_default_model("google") == "gemini-1.5-flash"

    def test_validate_config_valid(self):
        """Test validation of valid config."""
        parser = GitHubIssueParser()

        config = {
            "name": "test_agent",
            "role": "Test assistant",
            "tool_collections": ["research"],
            "llm_provider": "openai",
            "system_prompt": "You are helpful",
        }

        assert parser.validate_config(config) is True

    def test_validate_config_missing_fields(self):
        """Test validation fails with missing fields."""
        parser = GitHubIssueParser()

        config = {
            "name": "test_agent",
            "role": "Test assistant",
        }

        assert parser.validate_config(config) is False

    def test_validate_config_invalid_tool(self):
        """Test validation fails with invalid tool."""
        parser = GitHubIssueParser()

        config = {
            "name": "test_agent",
            "role": "Test assistant",
            "tool_collections": ["invalid_tool"],
            "llm_provider": "openai",
            "system_prompt": "You are helpful",
        }

        assert parser.validate_config(config) is False

    def test_validate_config_invalid_provider(self):
        """Test validation fails with invalid provider."""
        parser = GitHubIssueParser()

        config = {
            "name": "test_agent",
            "role": "Test assistant",
            "tool_collections": ["research"],
            "llm_provider": "invalid_provider",
            "system_prompt": "You are helpful",
        }

        assert parser.validate_config(config) is False

    def test_parse_issue_url_valid(self):
        """Test parsing valid GitHub issue URL."""
        parser = GitHubIssueParser()

        url = "https://github.com/user/repo/issues/42"
        result = parser.parse_issue_url(url)

        assert "source" in result
        assert "user/repo#42" in result["source"]

    def test_parse_issue_url_invalid(self):
        """Test parsing invalid URL raises error."""
        parser = GitHubIssueParser()

        with pytest.raises(ValueError):
            parser.parse_issue_url("https://github.com/user/repo")

    def test_normalize_tool_name(self):
        """Test tool name normalization."""
        parser = GitHubIssueParser()

        assert parser._normalize_tool_name("Research") == "research"
        assert parser._normalize_tool_name("Web Search") == "research"
        assert parser._normalize_tool_name("Coding Tools") == "coding"
        assert parser._normalize_tool_name("File Operations") == "file"
        assert parser._normalize_tool_name("Project Twin") == "twin"

    def test_extract_boolean_from_checkbox(self):
        """Test boolean extraction from checkbox."""
        parser = GitHubIssueParser()

        assert parser._extract_boolean("- [x] Enable") is True
        assert parser._extract_boolean("- [ ] Enable") is False

    def test_extract_boolean_from_text(self):
        """Test boolean extraction from text."""
        parser = GitHubIssueParser()

        assert parser._extract_boolean("Yes") is True
        assert parser._extract_boolean("true") is True
        assert parser._extract_boolean("enabled") is True
        assert parser._extract_boolean("No") is False
        assert parser._extract_boolean("false") is False
        assert parser._extract_boolean("disabled") is False


class TestGitHubAgentClient:
    """Tests for GitHubAgentClient class."""

    @patch('agent_factory.github.github_client.Github')
    def test_client_initialization_with_token(self, mock_github):
        """Test client initialization with explicit token."""
        mock_github_instance = MagicMock()
        mock_github.return_value = mock_github_instance

        client = GitHubAgentClient(token="ghp_test123")

        assert client.token == "ghp_test123"
        mock_github.assert_called_once_with("ghp_test123")

    @patch.dict('os.environ', {'GITHUB_TOKEN': 'ghp_env_token'})
    @patch('agent_factory.github.github_client.Github')
    def test_client_initialization_from_env(self, mock_github):
        """Test client initialization from environment variable."""
        mock_github_instance = MagicMock()
        mock_github.return_value = mock_github_instance

        client = GitHubAgentClient()

        assert client.token == "ghp_env_token"

    def test_client_initialization_no_token(self):
        """Test client initialization fails without token."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="GitHub token required"):
                GitHubAgentClient()

    @patch('agent_factory.github.github_client.Github')
    def test_get_issue_from_url(self, mock_github):
        """Test fetching issue from URL."""
        mock_github_instance = MagicMock()
        mock_repo = MagicMock()
        mock_issue = MagicMock()

        mock_github.return_value = mock_github_instance
        mock_github_instance.get_repo.return_value = mock_repo
        mock_repo.get_issue.return_value = mock_issue

        client = GitHubAgentClient(token="ghp_test")
        url = "https://github.com/owner/repo/issues/42"

        issue = client.get_issue_from_url(url)

        mock_github_instance.get_repo.assert_called_once_with("owner/repo")
        mock_repo.get_issue.assert_called_once_with(42)
        assert issue == mock_issue

    @patch('agent_factory.github.github_client.Github')
    def test_get_issue_from_url_invalid(self, mock_github):
        """Test fetching issue from invalid URL raises error."""
        mock_github_instance = MagicMock()
        mock_github.return_value = mock_github_instance

        client = GitHubAgentClient(token="ghp_test")

        with pytest.raises(ValueError, match="Invalid GitHub issue URL"):
            client.get_issue_from_url("https://github.com/owner/repo")

    @patch('agent_factory.github.github_client.Github')
    def test_format_agent_created_comment(self, mock_github):
        """Test formatting agent creation comment."""
        mock_github_instance = MagicMock()
        mock_github.return_value = mock_github_instance

        client = GitHubAgentClient(token="ghp_test")

        config = {
            "name": "research_bot",
            "role": "Research Assistant",
            "tool_collections": ["research", "file"],
            "llm_provider": "openai",
            "model": "gpt-4o-mini"
        }

        comment = client.format_agent_created_comment(config)

        assert "research_bot" in comment
        assert "Research Assistant" in comment
        assert "research, file" in comment
        assert "openai/gpt-4o-mini" in comment
        assert "agentcli chat --agent research_bot" in comment

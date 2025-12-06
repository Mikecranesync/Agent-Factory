"""
GitHub Issue Parser - Extract agent configurations from GitHub issues

Supports two parsing modes:
1. Template-based: Parse structured issue templates (YAML forms)
2. Freeform: Use LLM to extract agent specs from natural language

Usage:
    parser = GitHubIssueParser()
    config = parser.parse_issue_body(issue_body)
    config = parser.parse_issue_url("https://github.com/user/repo/issues/42")
"""

import re
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse


class GitHubIssueParser:
    """Parse GitHub issues to extract agent configurations."""

    # Template field markers (GitHub issue forms use ### headings)
    TEMPLATE_MARKERS = {
        "agent_name": ["agent name", "name"],
        "role": ["role/purpose", "role", "purpose"],
        "description": ["description"],
        "tool_collections": ["tool collections", "tools"],
        "llm_provider": ["llm provider", "provider"],
        "model": ["model"],
        "temperature": ["temperature"],
        "system_prompt": ["system prompt", "prompt"],
        "memory": ["memory"],
    }

    # Tool collection mappings
    TOOL_MAPPINGS = {
        "research": ["research", "web search", "wikipedia"],
        "file": ["file operations", "file", "files", "file ops"],
        "coding": ["coding", "code", "git"],
        "twin": ["twin", "codebase", "project twin", "code analysis"],
    }

    # LLM provider mappings
    PROVIDER_MAPPINGS = {
        "openai": ["openai", "gpt", "chatgpt"],
        "anthropic": ["anthropic", "claude"],
        "google": ["google", "gemini"],
    }

    def __init__(self):
        """Initialize issue parser."""
        self.llm = None  # Optional: LLM for freeform parsing

    def parse_issue_url(self, url: str) -> Dict[str, Any]:
        """
        Parse agent config from GitHub issue URL.

        Args:
            url: GitHub issue URL (e.g., https://github.com/user/repo/issues/42)

        Returns:
            Agent configuration dictionary

        Raises:
            ValueError: If URL is invalid
        """
        # Extract owner, repo, issue_number from URL
        parsed = urlparse(url)
        path_parts = parsed.path.strip("/").split("/")

        if len(path_parts) < 4 or path_parts[2] != "issues":
            raise ValueError(f"Invalid GitHub issue URL: {url}")

        owner = path_parts[0]
        repo = path_parts[1]
        issue_number = path_parts[3]

        # In real implementation, would fetch issue via GitHub API
        # For now, return placeholder
        return {
            "source": f"{owner}/{repo}#{issue_number}",
            "url": url,
            "note": "Fetch issue body via GitHubAgentClient.get_issue()",
        }

    def parse_issue_body(self, body: str) -> Dict[str, Any]:
        """
        Parse agent config from issue body.

        Automatically detects if issue uses template format or freeform.

        Args:
            body: Issue body text

        Returns:
            Agent configuration dictionary
        """
        # Detect format
        if self._is_template_format(body):
            return self._parse_template(body)
        else:
            return self._parse_freeform(body)

    def _is_template_format(self, body: str) -> bool:
        """Check if issue uses template format (has ### headings)."""
        body_lower = body.lower()
        return "###" in body and any(marker.lower() in body_lower for markers in self.TEMPLATE_MARKERS.values() for marker in markers)

    def _parse_template(self, body: str) -> Dict[str, Any]:
        """
        Parse structured issue template.

        Looks for ### headings and extracts values below them.

        Args:
            body: Issue body with template format

        Returns:
            Agent configuration dictionary
        """
        config = {}

        # Split by ### headings
        sections = re.split(r'\n### ', '\n' + body)

        for section in sections[1:]:  # Skip first empty section
            lines = section.strip().split('\n', 1)
            if len(lines) < 2:
                continue

            heading = lines[0].strip()
            content = lines[1].strip() if len(lines) > 1 else ""

            # Match heading to config field
            field_name = self._match_heading_to_field(heading)

            if field_name:
                # Extract value based on field type
                if field_name == "tool_collections":
                    config[field_name] = self._extract_tools(content)
                elif field_name == "llm_provider":
                    config[field_name] = self._extract_provider(content)
                elif field_name == "memory":
                    config["memory_enabled"] = self._extract_boolean(content)
                elif field_name == "temperature":
                    try:
                        config[field_name] = float(content)
                    except ValueError:
                        config[field_name] = 0.7  # Default
                else:
                    # Plain text field
                    config[field_name] = content

        # Apply defaults
        config = self._apply_defaults(config)

        return config

    def _parse_freeform(self, body: str) -> Dict[str, Any]:
        """
        Parse freeform issue using pattern matching and heuristics.

        Optionally uses LLM for intelligent extraction.

        Args:
            body: Issue body in natural language

        Returns:
            Agent configuration dictionary
        """
        config = {}

        # Extract agent name (look for patterns)
        name_match = re.search(r'(?:agent name|name):\s*([a-z_][a-z0-9_]*)', body, re.IGNORECASE)
        if name_match:
            config["name"] = name_match.group(1).lower().replace(" ", "_")

        # Extract role/purpose (first paragraph or explicit marker)
        role_match = re.search(r'(?:role|purpose):\s*(.+?)(?:\n\n|\n###|$)', body, re.IGNORECASE | re.DOTALL)
        if role_match:
            config["role"] = role_match.group(1).strip()
        else:
            # Use first non-empty line as role
            first_line = next((line.strip() for line in body.split('\n') if line.strip()), "")
            if first_line:
                config["role"] = first_line

        # Infer tools from keywords
        config["tool_collections"] = self._infer_tools(body)

        # Infer LLM provider
        config["llm_provider"] = self._infer_provider(body)

        # Extract system prompt if present
        prompt_match = re.search(r'(?:system prompt|prompt):\s*(.+?)(?:\n\n|\n###|$)', body, re.IGNORECASE | re.DOTALL)
        if prompt_match:
            config["system_prompt"] = prompt_match.group(1).strip()

        # Apply defaults
        config = self._apply_defaults(config)

        return config

    def _match_heading_to_field(self, heading: str) -> Optional[str]:
        """Match template heading to config field name."""
        heading_lower = heading.lower()

        for field, markers in self.TEMPLATE_MARKERS.items():
            if any(marker.lower() in heading_lower for marker in markers):
                return field

        return None

    def _extract_tools(self, content: str) -> List[str]:
        """Extract tool collections from checkboxes or text."""
        tools = []

        # Look for checked boxes: - [x] Research
        checked_boxes = re.findall(r'-\s*\[x\]\s*(.+?)(?:\(|$)', content, re.IGNORECASE | re.MULTILINE)

        for box_text in checked_boxes:
            tool = self._normalize_tool_name(box_text.strip())
            if tool:
                tools.append(tool)

        # If no checkboxes, look for comma-separated list
        if not tools:
            for tool_key, keywords in self.TOOL_MAPPINGS.items():
                if any(kw in content.lower() for kw in keywords):
                    tools.append(tool_key)

        return tools

    def _extract_provider(self, content: str) -> str:
        """Extract LLM provider from dropdown or text."""
        content_lower = content.lower()

        for provider, keywords in self.PROVIDER_MAPPINGS.items():
            if any(kw in content_lower for kw in keywords):
                return provider

        return "openai"  # Default

    def _extract_boolean(self, content: str) -> bool:
        """Extract boolean from checkbox or text."""
        content_lower = content.lower()

        # Check for unchecked box first (more specific)
        if "[ ]" in content:
            return False

        # Check for checked box
        if "[x]" in content or "[X]" in content:
            return True

        # Check for no/false/disabled (check negative first)
        if any(word in content_lower for word in ["no", "false", "disabled", "disable"]):
            return False

        # Check for yes/true/enabled
        if any(word in content_lower for word in ["yes", "true", "enabled", "enable"]):
            return True

        return True  # Default to enabled

    def _normalize_tool_name(self, text: str) -> Optional[str]:
        """Normalize tool name from text to standard key."""
        text_lower = text.lower()

        for tool_key, keywords in self.TOOL_MAPPINGS.items():
            if any(kw in text_lower for kw in keywords):
                return tool_key

        return None

    def _infer_tools(self, body: str) -> List[str]:
        """Infer tool collections from body content using keywords."""
        tools = []
        body_lower = body.lower()

        for tool_key, keywords in self.TOOL_MAPPINGS.items():
            if any(kw in body_lower for kw in keywords):
                tools.append(tool_key)

        # Default to research if no tools detected
        if not tools:
            tools = ["research"]

        return tools

    def _infer_provider(self, body: str) -> str:
        """Infer LLM provider from body content."""
        body_lower = body.lower()

        for provider, keywords in self.PROVIDER_MAPPINGS.items():
            if any(kw in body_lower for kw in keywords):
                return provider

        return "openai"  # Default

    def _apply_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply default values for missing fields."""
        # Generate name from agent_name or role
        if "agent_name" in config and config["agent_name"]:
            name = config["agent_name"].lower().replace(" ", "_")[:30]
        elif "name" in config and config["name"]:
            name = config["name"]
        else:
            name = config.get("role", "custom_agent").lower().replace(" ", "_")[:30]

        defaults = {
            "name": name,
            "description": config.get("role", "A custom AI agent"),
            "tool_collections": config.get("tool_collections") or ["research"],
            "llm_provider": config.get("llm_provider", "openai"),
            "model": self._get_default_model(config.get("llm_provider", "openai")),
            "temperature": config.get("temperature", 0.7),
            "agent_type": "react",
            "system_prompt": config.get("system_prompt") or f"You are a helpful {config.get('role', 'AI assistant')}.",
            "memory_enabled": config.get("memory_enabled", True),
        }

        # Merge with config (config takes precedence)
        final_config = {**defaults, **config}

        # Remove agent_name if it exists (we've converted it to name)
        final_config.pop("agent_name", None)

        return final_config

    def _get_default_model(self, provider: str) -> str:
        """Get default model for LLM provider."""
        model_defaults = {
            "openai": "gpt-4o-mini",
            "anthropic": "claude-3-5-sonnet-20241022",
            "google": "gemini-1.5-flash",
        }
        return model_defaults.get(provider, "gpt-4o-mini")

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate agent configuration.

        Args:
            config: Agent configuration dictionary

        Returns:
            True if valid, False otherwise
        """
        required_fields = ["name", "role", "tool_collections", "llm_provider", "system_prompt"]

        for field in required_fields:
            if field not in config or not config[field]:
                return False

        # Validate tool collections
        valid_tools = set(self.TOOL_MAPPINGS.keys())
        for tool in config["tool_collections"]:
            if tool not in valid_tools:
                return False

        # Validate provider
        if config["llm_provider"] not in self.PROVIDER_MAPPINGS.keys():
            return False

        return True

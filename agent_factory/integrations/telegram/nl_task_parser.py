"""Natural Language Task Parser for SCAFFOLD Integration

Converts natural language task descriptions into structured TaskSpec format
using Claude 3.5 Sonnet for intelligent extraction.

Usage:
    parser = NLTaskParser(anthropic_api_key="...")
    task_spec = parser.parse_nl_to_task("Build login with email validation")
"""

from anthropic import Anthropic
import json
import os
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class NLTaskParser:
    """Parse natural language into structured task specifications"""

    def __init__(self, anthropic_api_key: Optional[str] = None):
        """Initialize parser with Anthropic API client

        Args:
            anthropic_api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
        """
        api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found. "
                "Set environment variable or pass anthropic_api_key parameter."
            )

        self.client = Anthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-20241022"

    def parse_nl_to_task(self, description: str) -> Dict:
        """Convert natural language description to TaskSpec dict

        Args:
            description: Natural language task description

        Returns:
            TaskSpec-compatible dict with:
                - title: str (ACTION: Brief description)
                - description: str (Detailed description)
                - acceptance_criteria: List[str] (Testable criteria)
                - priority: str (high|medium|low)
                - labels: List[str] (Categorization tags)

        Raises:
            ValueError: If description is empty
            Exception: If API call fails or JSON parsing fails

        Example:
            >>> parser = NLTaskParser()
            >>> task = parser.parse_nl_to_task("Build login with OAuth")
            >>> print(task['title'])
            'BUILD: Login System with OAuth'
        """
        if not description or not description.strip():
            raise ValueError("Task description cannot be empty")

        logger.info(f"Parsing natural language task: {description[:100]}...")

        try:
            # Build extraction prompt
            prompt = self._build_extraction_prompt(description)

            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                temperature=0,  # Deterministic for consistent extraction
                messages=[{"role": "user", "content": prompt}]
            )

            # Extract JSON from response
            response_text = response.content[0].text.strip()

            # Handle code blocks (```json ... ```)
            if response_text.startswith("```"):
                # Extract content between code fences
                lines = response_text.split("\n")
                json_lines = []
                in_code = False

                for line in lines:
                    if line.startswith("```"):
                        in_code = not in_code
                        continue
                    if in_code:
                        json_lines.append(line)

                response_text = "\n".join(json_lines)

            # Parse JSON
            task_spec = json.loads(response_text)

            # Validate required fields
            self._validate_task_spec(task_spec)

            # Add metadata
            task_spec['labels'] = task_spec.get('labels', []) + ['telegram-trigger']
            task_spec['labels'] = list(set(task_spec['labels']))  # Remove duplicates

            logger.info(f"Successfully parsed task: {task_spec['title']}")

            return task_spec

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response text: {response_text}")
            raise Exception(f"Failed to parse task specification: Invalid JSON format")

        except Exception as e:
            logger.error(f"Failed to parse natural language task: {e}")
            raise

    def _build_extraction_prompt(self, description: str) -> str:
        """Build prompt for task extraction

        Args:
            description: User's natural language description

        Returns:
            Formatted prompt for Claude
        """
        return f"""Extract a structured task specification from this user request:

"{description}"

Return ONLY valid JSON (no markdown, no explanations) with this exact structure:
{{
    "title": "ACTION: Brief description (max 80 chars)",
    "description": "Detailed description (200+ words explaining what needs to be built/fixed/tested)",
    "acceptance_criteria": [
        "Testable criterion 1",
        "Testable criterion 2",
        "Testable criterion 3"
    ],
    "priority": "high|medium|low",
    "labels": ["category1", "category2"]
}}

RULES:
1. Title MUST start with action verb: BUILD, FIX, TEST, DOCS, REFACTOR, DEPLOY, etc.
2. Description should be detailed enough for autonomous implementation (200+ words)
3. Acceptance criteria MUST be testable/verifiable (3-5 items minimum)
4. Priority guidelines:
   - high: Critical bugs, security issues, blocking work
   - medium: New features, enhancements, non-blocking bugs
   - low: Nice-to-haves, optimizations, minor improvements
5. Labels: Categorize by type and domain (e.g., ["auth", "backend", "api", "build"])

EXAMPLES:

Input: "Build login with email validation"
Output:
{{
    "title": "BUILD: Login System with Email Validation",
    "description": "Implement a complete user authentication system with email/password login. The system should include email validation (both format and domain verification), secure password storage using bcrypt hashing, session management with JWT tokens, and proper error handling for invalid credentials. The implementation should follow security best practices including rate limiting for login attempts and HTTPS-only cookie handling.",
    "acceptance_criteria": [
        "Email validation working (regex + DNS check)",
        "Password hashed with bcrypt (min 10 rounds)",
        "Login endpoint returns valid JWT token",
        "Failed login attempts rate-limited (5 attempts per 15 min)",
        "Tests passing for all auth flows (login, logout, token refresh)"
    ],
    "priority": "high",
    "labels": ["auth", "backend", "security", "build"]
}}

Input: "Fix the bug where users can't upload images"
Output:
{{
    "title": "FIX: Image Upload Failure Bug",
    "description": "Users are experiencing failures when attempting to upload images through the web interface. Investigation needed to identify the root cause (likely file size limits, MIME type validation, or server configuration). Fix should handle all common image formats (JPEG, PNG, GIF, WebP), implement proper file size validation, add meaningful error messages for users, and include server-side security checks to prevent malicious uploads.",
    "acceptance_criteria": [
        "Users can upload JPEG, PNG, GIF, WebP images up to 10MB",
        "Proper error messages shown for unsupported formats/sizes",
        "Server-side validation prevents executable file uploads",
        "Upload progress indicator works correctly",
        "Existing tests updated and new tests added for upload scenarios"
    ],
    "priority": "high",
    "labels": ["bug", "upload", "media", "fix"]
}}

Now process the user's request above and return ONLY the JSON."""

    def _validate_task_spec(self, task_spec: Dict) -> None:
        """Validate that task_spec has all required fields

        Args:
            task_spec: Parsed task specification

        Raises:
            ValueError: If required fields are missing or invalid
        """
        required_fields = ['title', 'description', 'acceptance_criteria', 'priority', 'labels']

        for field in required_fields:
            if field not in task_spec:
                raise ValueError(f"Missing required field: {field}")

        # Validate title format
        title = task_spec['title']
        if not any(title.startswith(action + ":") for action in [
            "BUILD", "FIX", "TEST", "DOCS", "REFACTOR", "DEPLOY", "OPTIMIZE", "CLEANUP"
        ]):
            logger.warning(f"Title doesn't start with standard action verb: {title}")

        # Validate priority
        if task_spec['priority'] not in ['high', 'medium', 'low']:
            raise ValueError(f"Invalid priority: {task_spec['priority']}. Must be high, medium, or low.")

        # Validate acceptance criteria
        if not isinstance(task_spec['acceptance_criteria'], list):
            raise ValueError("acceptance_criteria must be a list")

        if len(task_spec['acceptance_criteria']) < 3:
            raise ValueError("At least 3 acceptance criteria required")

        # Validate labels
        if not isinstance(task_spec['labels'], list):
            raise ValueError("labels must be a list")

        if len(task_spec['labels']) < 1:
            raise ValueError("At least 1 label required")

    def estimate_cost(self, description: str) -> float:
        """Estimate cost of parsing this description

        Args:
            description: Task description

        Returns:
            Estimated cost in USD (rough approximation)
        """
        # Claude 3.5 Sonnet pricing (as of Dec 2024):
        # Input: $3/million tokens (~$0.000003/token)
        # Output: $15/million tokens (~$0.000015/token)

        # Rough token estimate: ~1.3 tokens per word
        input_tokens = len(description.split()) * 1.3 + 500  # +500 for prompt template
        output_tokens = 300  # Typical JSON response

        input_cost = (input_tokens / 1_000_000) * 3
        output_cost = (output_tokens / 1_000_000) * 15

        return input_cost + output_cost


# Convenience function for quick testing
def parse_task(description: str, api_key: Optional[str] = None) -> Dict:
    """Quick helper function for testing

    Args:
        description: Natural language task description
        api_key: Optional Anthropic API key

    Returns:
        TaskSpec dict

    Example:
        >>> task = parse_task("Build login feature")
        >>> print(task['title'])
    """
    parser = NLTaskParser(api_key)
    return parser.parse_nl_to_task(description)


if __name__ == "__main__":
    # Quick test
    import sys

    if len(sys.argv) < 2:
        print("Usage: python nl_task_parser.py '<task description>'")
        print("Example: python nl_task_parser.py 'Build login with OAuth'")
        sys.exit(1)

    description = " ".join(sys.argv[1:])

    try:
        parser = NLTaskParser()
        task_spec = parser.parse_nl_to_task(description)

        print("\n=== Parsed Task Specification ===\n")
        print(json.dumps(task_spec, indent=2))

        print(f"\n=== Estimated Cost ===")
        print(f"${parser.estimate_cost(description):.4f} USD")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

"""
GitHub Integration Demo

Demonstrates:
1. Parsing issue templates to extract agent configs
2. Parsing freeform issues
3. Creating agents from parsed configs
4. GitHub workflow simulation

Run:
    poetry run python agent_factory/examples/github_demo.py
"""

from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

from agent_factory.github import GitHubIssueParser
from agent_factory.core.agent_factory import AgentFactory


def demo_template_parsing():
    """Demo 1: Parse a template-based GitHub issue."""
    print("\n" + "=" * 70)
    print("DEMO 1: Template-based Issue Parsing")
    print("=" * 70)

    # Simulated issue body from GitHub issue template
    issue_body = """
### Agent Name
research_assistant

### Role/Purpose
A specialized AI research assistant that helps with academic research,
literature reviews, and fact-checking.

### Tool Collections
- [x] Research (web search, Wikipedia)
- [ ] Coding
- [x] File Operations
- [ ] Twin

### LLM Provider
Anthropic Claude

### Model
claude-3-5-sonnet-20241022

### Temperature
0.3

### System Prompt
You are a meticulous research assistant specialized in academic research.
Always cite your sources and cross-reference information.
Use a professional, scholarly tone.

### Memory
- [x] Enable conversation memory
    """

    print("\nIssue Body:")
    print("-" * 70)
    print(issue_body)
    print("-" * 70)

    # Parse issue
    parser = GitHubIssueParser()
    config = parser.parse_issue_body(issue_body)

    print("\nExtracted Configuration:")
    print(f"  Name: {config['name']}")
    print(f"  Role: {config['role']}")
    print(f"  Tools: {', '.join(config['tool_collections'])}")
    print(f"  LLM: {config['llm_provider']}/{config['model']}")
    print(f"  Temperature: {config['temperature']}")
    print(f"  Memory: {config['memory_enabled']}")
    print(f"\nSystem Prompt:\n  {config['system_prompt'][:100]}...")

    # Validate
    is_valid = parser.validate_config(config)
    print(f"\nValidation: {'[PASS]' if is_valid else '[FAIL]'}")

    return config


def demo_freeform_parsing():
    """Demo 2: Parse a freeform GitHub issue."""
    print("\n" + "=" * 70)
    print("DEMO 2: Freeform Issue Parsing")
    print("=" * 70)

    # Simulated freeform issue
    issue_body = """
I need an agent that can help me with coding tasks. It should be able to:

- Read and write files in my project
- Search through code to find functions and classes
- Use the project twin to understand the codebase structure

Please use GPT-4 for this since it's good at code. Make it temperature 0.2
so it's more precise.

Agent name: code_buddy

Role: A coding assistant that helps with refactoring and code review
    """

    print("\nIssue Body:")
    print("-" * 70)
    print(issue_body)
    print("-" * 70)

    # Parse issue
    parser = GitHubIssueParser()
    config = parser.parse_issue_body(issue_body)

    print("\nExtracted Configuration:")
    print(f"  Name: {config['name']}")
    print(f"  Role: {config['role']}")
    print(f"  Tools: {', '.join(config['tool_collections'])}")
    print(f"  LLM: {config['llm_provider']}/{config['model']}")
    print(f"  Temperature: {config['temperature']}")

    # Validate
    is_valid = parser.validate_config(config)
    print(f"\nValidation: {'[PASS]' if is_valid else '[FAIL]'}")

    return config


def demo_agent_creation(config):
    """Demo 3: Create an agent from parsed config."""
    print("\n" + "=" * 70)
    print("DEMO 3: Create Agent from Config")
    print("=" * 70)

    print(f"\nCreating agent: {config['name']}")
    print(f"  Role: {config['role']}")

    try:
        # Note: This requires valid API keys in environment
        # For demo purposes, we'll show the process
        factory = AgentFactory()

        # Map tool collections to tool instances
        tool_collections = config.get("tool_collections", [])

        print(f"\n  Loading tools: {', '.join(tool_collections)}")

        # Create agent (this will fail if API keys not set, which is fine for demo)
        try:
            agent = factory.create_agent(
                role=config["role"],
                tools_list=[],  # Would be populated based on tool_collections
                system_prompt=config.get("system_prompt", ""),
                llm_provider=config.get("llm_provider", "openai"),
                model=config.get("model"),
                temperature=config.get("temperature", 0.7),
                memory_enabled=config.get("memory_enabled", True)
            )

            print(f"\n[OK] Agent created successfully!")
            print(f"  Type: {type(agent).__name__}")
            print(f"  Tools: {len(agent.tools)} loaded")

        except Exception as e:
            # Expected if API keys not configured
            print(f"\n[SKIP] Agent creation skipped (API keys not configured)")
            print(f"  In production, agent would be created with:")
            print(f"    - Role: {config['role']}")
            print(f"    - LLM: {config['llm_provider']}/{config['model']}")
            print(f"    - Temperature: {config['temperature']}")
            print(f"    - Tools: {', '.join(tool_collections)}")

    except Exception as e:
        print(f"\n✗ Error: {str(e)}")


def demo_multiple_issue_formats():
    """Demo 4: Parse various issue formats."""
    print("\n" + "=" * 70)
    print("DEMO 4: Multiple Issue Formats")
    print("=" * 70)

    test_cases = [
        {
            "name": "Minimal Template",
            "body": """
### Agent Name
simple_agent

### Role
A simple helper agent
            """
        },
        {
            "name": "One-liner Request",
            "body": "Create a research agent using Claude"
        },
        {
            "name": "Detailed Request",
            "body": """
Name: data_analyzer
Role: Data analysis assistant

I need an agent that can analyze datasets and create visualizations.
Use GPT-4 and enable memory.
            """
        }
    ]

    parser = GitHubIssueParser()

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print("-" * 70)
        print(f"Body: {test_case['body'][:80]}...")

        config = parser.parse_issue_body(test_case["body"])
        is_valid = parser.validate_config(config)

        print(f"  -> Name: {config['name']}")
        print(f"  -> Role: {config['role'][:60]}...")
        print(f"  -> Valid: {'[OK]' if is_valid else '[FAIL]'}")


def demo_github_workflow():
    """Demo 5: Simulated GitHub Actions workflow."""
    print("\n" + "=" * 70)
    print("DEMO 5: GitHub Actions Workflow Simulation")
    print("=" * 70)

    print("\nSimulated workflow:")
    print("  1. Issue created with '@claude create agent' label")
    print("  2. GitHub Action triggered")
    print("  3. Issue body fetched")
    print("  4. Agent config parsed")
    print("  5. Agent created and stored")
    print("  6. Success comment posted")

    # Simulate issue
    issue_body = """
### Agent Name
deployment_helper

### Role
Helps with deployment and DevOps tasks

### Tool Collections
- [x] Coding
- [x] File Operations
    """

    print("\n-> Parsing issue...")
    parser = GitHubIssueParser()
    config = parser.parse_issue_body(issue_body)

    print("-> Validating config...")
    is_valid = parser.validate_config(config)

    if is_valid:
        print("-> Creating agent...")
        print(f"-> Agent '{config['name']}' created successfully")

        # Simulate comment formatting
        from agent_factory.github import GitHubAgentClient

        # Mock client (no API call)
        mock_client = type('MockClient', (), {})()
        mock_client.format_agent_created_comment = GitHubAgentClient.format_agent_created_comment.__get__(mock_client)

        comment = mock_client.format_agent_created_comment(config)

        print("\n-> Comment to post:")
        print("-" * 70)
        print(comment[:300])
        print("...")
        print("-" * 70)

        print("\n[OK] Workflow completed successfully")
    else:
        print("\n[FAIL] Validation failed - would post error comment")


def main():
    """Run all demos."""
    print("\n" + "=" * 70)
    print("GitHub Integration Demo")
    print("Agent Factory - Create agents from GitHub issues")
    print("=" * 70)

    # Demo 1: Template parsing
    template_config = demo_template_parsing()

    # Demo 2: Freeform parsing
    freeform_config = demo_freeform_parsing()

    # Demo 3: Agent creation
    demo_agent_creation(template_config)

    # Demo 4: Multiple formats
    demo_multiple_issue_formats()

    # Demo 5: GitHub workflow
    demo_github_workflow()

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("\nGitHub Integration supports:")
    print("  [+] Template-based issues (structured forms)")
    print("  [+] Freeform issues (natural language)")
    print("  [+] Automatic tool detection")
    print("  [+] LLM provider inference")
    print("  [+] Config validation")
    print("  [+] GitHub Actions integration")
    print("\nUsage:")
    print("  1. Create GitHub issue (template or freeform)")
    print("  2. Add '@claude create agent' label")
    print("  3. GitHub Action parses and creates agent")
    print("  4. Agent config committed to .agent_factory/agents/")
    print("  5. Local users sync with: agentcli github-sync")
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()

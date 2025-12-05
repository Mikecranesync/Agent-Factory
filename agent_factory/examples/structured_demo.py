"""
Structured Outputs Demo - Type-safe agent responses

Demonstrates:
1. Agents with response schemas (ResearchResponse, CodeResponse, CreativeResponse)
2. Type-safe response access
3. Pydantic validation
4. Backwards compatibility (agents without schemas)
"""
import os
import sys
from pathlib import Path

# Add parent to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from agent_factory.core import AgentFactory
from agent_factory.schemas import (
    AgentResponse,
    ResearchResponse,
    CodeResponse,
    CreativeResponse,
)
from agent_factory.tools.research_tools import CurrentTimeTool


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'=' * 60}")
    print(f"{title}")
    print("=" * 60)


def print_response(label: str, response: any):
    """Print a response with formatting."""
    print(f"\n{label}:")
    print(f"  Type: {type(response).__name__}")

    if isinstance(response, AgentResponse):
        # It's a Pydantic model - show structured fields
        print(f"  Success: {response.success}")
        print(f"  Output: {response.output[:150]}..." if len(response.output) > 150 else f"  Output: {response.output}")

        # Show type-specific fields
        if isinstance(response, ResearchResponse):
            print(f"  Confidence: {response.confidence}")
            print(f"  Sources: {response.sources}")
        elif isinstance(response, CodeResponse):
            print(f"  Language: {response.language}")
            print(f"  Code snippet: {response.code[:100]}...")
        elif isinstance(response, CreativeResponse):
            print(f"  Genre: {response.genre}")
            print(f"  Style: {response.style}")
            print(f"  Word count: {response.word_count}")

        print(f"  Metadata: {response.metadata}")
        print(f"  Timestamp: {response.timestamp}")
    else:
        # Raw dict response (backwards compatibility)
        print(f"  Raw response: {str(response)[:200]}...")


def main():
    print_section("STRUCTURED OUTPUTS DEMO")

    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("\n[WARNING] OPENAI_API_KEY not found in environment variables")
        print("   Please set it in your .env file or environment")
        print("   Example: export OPENAI_API_KEY='your-api-key-here'\n")
        return

    # Create factory
    factory = AgentFactory(verbose=False)

    # Create a simple tool for agents
    time_tool = CurrentTimeTool()

    print_section("1. Research Agent with ResearchResponse")

    # Create research agent WITH schema
    research_agent = factory.create_agent(
        role="Research Specialist",
        tools_list=[time_tool],
        system_prompt="You are a research assistant. Answer questions with facts.",
        enable_memory=False,
        response_schema=ResearchResponse  # Type-safe responses!
    )

    print("\nAgent created with response_schema=ResearchResponse")
    print("Schema ensures responses have: success, output, sources, confidence")

    # Invoke agent
    result = research_agent.invoke({"input": "What is the capital of France?"})

    # Parse result
    orchestrator = factory.create_orchestrator(verbose=False)
    orchestrator.register("research", research_agent, keywords=["capital"])

    route_result = orchestrator.route("What is the capital of France?")

    print_response("Research agent response", route_result.response)

    print_section("2. Code Agent with CodeResponse")

    # Create code agent WITH schema
    code_agent = factory.create_agent(
        role="Code Assistant",
        tools_list=[time_tool],
        system_prompt="You are a coding assistant. Help with programming.",
        enable_memory=False,
        response_schema=CodeResponse  # Type-safe code responses!
    )

    print("\nAgent created with response_schema=CodeResponse")
    print("Schema ensures responses have: success, output, code, language, explanation")

    orchestrator.register("coding", code_agent, keywords=["code", "function"])
    route_result = orchestrator.route("Write a Python function to check if a number is prime")

    print_response("Code agent response", route_result.response)

    print_section("3. Creative Agent with CreativeResponse")

    # Create creative agent WITH schema
    creative_agent = factory.create_agent(
        role="Creative Writer",
        tools_list=[time_tool],
        system_prompt="You are a creative writer. Write stories and poems.",
        enable_memory=False,
        response_schema=CreativeResponse  # Type-safe creative responses!
    )

    print("\nAgent created with response_schema=CreativeResponse")
    print("Schema ensures responses have: success, output, genre, style, word_count")

    orchestrator.register("creative", creative_agent, keywords=["poem", "story", "write"])
    route_result = orchestrator.route("Write a short haiku about AI")

    print_response("Creative agent response", route_result.response)

    print_section("4. Generic Agent WITHOUT schema (Backwards Compatible)")

    # Create agent WITHOUT schema - should still work!
    generic_agent = factory.create_agent(
        role="Generic Assistant",
        tools_list=[time_tool],
        system_prompt="You are a helpful assistant.",
        enable_memory=False
        # No response_schema specified
    )

    print("\nAgent created WITHOUT response_schema")
    print("Returns raw dict response (backwards compatible)")

    orchestrator.register("generic", generic_agent, keywords=["hello"])
    route_result = orchestrator.route("Hello, how are you?")

    print_response("Generic agent response", route_result.response)

    print_section("5. Type Safety Demonstration")

    print("\nWith schemas, IDEs provide autocomplete:")
    print("  response.success     # Boolean")
    print("  response.output      # String")
    print("  response.metadata    # Dict")
    print("  response.timestamp   # datetime")
    print("")
    print("Specialized fields:")
    print("  ResearchResponse.confidence   # Float (0.0-1.0)")
    print("  ResearchResponse.sources      # List[str]")
    print("  CodeResponse.language         # String")
    print("  CodeResponse.code             # String")
    print("  CreativeResponse.genre        # String")
    print("  CreativeResponse.word_count   # Int")

    print_section("6. Validation Example")

    print("\nPydantic automatically validates:")
    try:
        # Valid response
        valid = ResearchResponse(
            success=True,
            output="Paris is the capital",
            confidence=0.95,
            sources=["Wikipedia"]
        )
        print(f"[OK] Valid response created: {valid.success}")

        # Invalid confidence (must be 0.0-1.0)
        invalid = ResearchResponse(
            success=True,
            output="Test",
            confidence=1.5,  # Invalid! Must be <= 1.0
            sources=[]
        )
    except Exception as e:
        print(f"[VALIDATION ERROR] {e}")

    print_section("DEMO COMPLETE")
    print("\nKey Takeaways:")
    print("  1. Type-safe responses with Pydantic schemas")
    print("  2. IDE autocomplete for response fields")
    print("  3. Automatic validation (confidence 0.0-1.0, etc.)")
    print("  4. Backwards compatible (agents without schemas work)")
    print("  5. Extensible (create custom response types)")


if __name__ == "__main__":
    main()

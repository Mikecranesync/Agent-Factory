"""
twin_demo.py - Demonstration of Project Twin capabilities

Shows how to:
1. Create and sync a project twin
2. Query project structure
3. Find dependencies
4. Use the Twin Agent with LLM
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agent_factory.refs import ProjectTwin, TwinAgent
from agent_factory.core import AgentFactory


def demo_basic_twin():
    """Demo 1: Basic twin creation and sync."""
    print("=" * 60)
    print("DEMO 1: Basic Project Twin")
    print("=" * 60)

    # Create twin
    project_root = Path.cwd()
    twin = ProjectTwin(project_root=project_root)

    # Sync with project (Python files only)
    print(f"\nSyncing with project at: {project_root}")
    twin.sync(
        include_patterns=["*.py"],
        exclude_patterns=["**/__pycache__/**", "**/tests/**", "**/.venv/**"]
    )

    print(f"Synced {len(twin.files)} Python files")
    print(f"Found {len(twin.class_map)} classes")
    print(f"Found {len(twin.function_map)} functions")
    print(f"Last sync: {twin.last_sync}")


def demo_file_queries(twin: ProjectTwin):
    """Demo 2: Query files by purpose."""
    print("\n" + "=" * 60)
    print("DEMO 2: Finding Files by Purpose")
    print("=" * 60)

    # Find files by purpose
    purposes = ["agent", "tool", "schema", "test"]

    for purpose in purposes:
        files = twin.find_files_by_purpose(purpose)
        print(f"\n'{purpose}' files ({len(files)}):")
        for file in files[:5]:  # Show first 5
            print(f"  - {file}")
        if len(files) > 5:
            print(f"  ... and {len(files) - 5} more")


def demo_dependencies(twin: ProjectTwin):
    """Demo 3: Explore dependencies."""
    print("\n" + "=" * 60)
    print("DEMO 3: Dependency Analysis")
    print("=" * 60)

    # Find orchestrator file
    orchestrator_path = None
    for file_path in twin.files.keys():
        if "orchestrator.py" in str(file_path):
            orchestrator_path = file_path
            break

    if orchestrator_path:
        print(f"\nAnalyzing: {orchestrator_path}")

        # Get dependencies
        deps = twin.get_dependencies(orchestrator_path)
        print(f"\nDependencies ({len(deps)}):")
        for dep in deps:
            print(f"  - {dep}")

        # Get dependents
        dependents = twin.get_dependents(orchestrator_path)
        print(f"\nDepended upon by ({len(dependents)}):")
        for dep in dependents:
            print(f"  - {dep}")
    else:
        print("orchestrator.py not found")


def demo_class_search(twin: ProjectTwin):
    """Demo 4: Search for classes and functions."""
    print("\n" + "=" * 60)
    print("DEMO 4: Class and Function Search")
    print("=" * 60)

    # Search for classes
    search_terms = ["Agent", "Twin", "Tool"]

    for term in search_terms:
        matches = {
            cls: path
            for cls, path in twin.class_map.items()
            if term.lower() in cls.lower()
        }

        if matches:
            print(f"\nClasses containing '{term}':")
            for cls, path in list(matches.items())[:3]:  # Show first 3
                print(f"  - {cls} in {path}")


def demo_file_summary(twin: ProjectTwin):
    """Demo 5: Get detailed file summary."""
    print("\n" + "=" * 60)
    print("DEMO 5: Detailed File Summary")
    print("=" * 60)

    # Get summary of agent_factory.py
    factory_path = None
    for file_path in twin.files.keys():
        if "agent_factory.py" in str(file_path):
            factory_path = file_path
            break

    if factory_path:
        summary = twin.get_file_summary(factory_path)
        print(f"\n{summary}")
    else:
        print("agent_factory.py not found")


def demo_natural_language_queries(twin: ProjectTwin):
    """Demo 6: Natural language queries."""
    print("\n" + "=" * 60)
    print("DEMO 6: Natural Language Queries")
    print("=" * 60)

    queries = [
        "Where is AgentFactory defined?",
        "Where is the EventBus class?",
        "What depends on callbacks.py?",
    ]

    for query in queries:
        print(f"\nQ: {query}")
        answer = twin.query(query)
        print(f"A: {answer}")


def demo_twin_agent_with_llm():
    """Demo 7: Twin Agent with LLM (requires API key)."""
    print("\n" + "=" * 60)
    print("DEMO 7: Twin Agent with LLM")
    print("=" * 60)

    try:
        # Create factory with LLM
        factory = AgentFactory()

        # Create twin
        project_root = Path.cwd()
        twin = ProjectTwin(project_root=project_root)
        twin.sync(
            include_patterns=["*.py"],
            exclude_patterns=["**/__pycache__/**", "**/tests/**"]
        )

        # Create twin agent with LLM
        twin_agent = TwinAgent(project_twin=twin, llm=factory._create_llm())

        # Ask natural language questions
        questions = [
            "Show me all the core modules",
            "What are the main classes in the orchestrator?",
        ]

        for question in questions:
            print(f"\nQ: {question}")
            try:
                answer = twin_agent.query(question)
                print(f"A: {answer}")
            except Exception as e:
                print(f"Error: {e}")

    except Exception as e:
        print(f"LLM demo skipped (API key may not be configured): {e}")


def main():
    """Run all demos."""
    print("\n")
    print("*" * 60)
    print(" PROJECT TWIN DEMONSTRATION")
    print("*" * 60)

    # Create and sync twin
    project_root = Path.cwd()
    twin = ProjectTwin(project_root=project_root)
    twin.sync(
        include_patterns=["*.py"],
        exclude_patterns=["**/__pycache__/**", "**/tests/**", "**/.venv/**", "**/build/**"]
    )

    # Run demos
    demo_basic_twin()
    demo_file_queries(twin)
    demo_dependencies(twin)
    demo_class_search(twin)
    demo_file_summary(twin)
    demo_natural_language_queries(twin)
    demo_twin_agent_with_llm()

    print("\n" + "=" * 60)
    print("All demos completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()

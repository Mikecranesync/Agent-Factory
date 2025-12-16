"""
Quick Test - Verify LangGraph Workflows Work

Tests that the workflow infrastructure is correctly set up
without requiring API keys or external services.
"""

from agent_factory.workflows import (
    GraphOrchestrator,
    create_research_workflow,
    create_consensus_workflow,
    create_supervisor_workflow,
    SharedAgentMemory
)

def test_imports():
    """Test that all workflow components import correctly"""
    print("Testing imports...")

    assert GraphOrchestrator is not None
    assert create_research_workflow is not None
    assert create_consensus_workflow is not None
    assert create_supervisor_workflow is not None
    assert SharedAgentMemory is not None

    print("✓ All imports successful")


def test_orchestrator_creation():
    """Test that GraphOrchestrator can be instantiated"""
    print("\nTesting GraphOrchestrator creation...")

    orch = GraphOrchestrator(verbose=False)
    assert orch is not None
    assert hasattr(orch, 'create_research_workflow')

    print("✓ GraphOrchestrator created successfully")


def test_workflow_structure():
    """Test that workflows can be created (without running)"""
    print("\nTesting workflow structure...")

    # Mock agents for testing
    class MockAgent:
        def __init__(self, name):
            self.name = name
            self.metadata = {"role": name}

        def invoke(self, input_dict):
            return {"output": f"Mock response from {self.name}"}

    # Test consensus workflow creation
    workflow = create_consensus_workflow(
        agents={
            "solvers": [MockAgent("solver1"), MockAgent("solver2")],
            "judge": MockAgent("judge")
        },
        verbose=False
    )

    assert workflow is not None
    print("✓ Consensus workflow created")

    # Test supervisor workflow creation
    workflow = create_supervisor_workflow(
        agents={
            "supervisor": MockAgent("supervisor"),
            "teams": {
                "research": MockAgent("research_team"),
                "analysis": MockAgent("analysis_team")
            }
        },
        verbose=False
    )

    assert workflow is not None
    print("✓ Supervisor workflow created")

    # Test research workflow creation
    orch = GraphOrchestrator(verbose=False)
    workflow = orch.create_research_workflow(
        agents={
            "planner": MockAgent("planner"),
            "researcher": MockAgent("researcher"),
            "analyzer": MockAgent("analyzer"),
            "writer": MockAgent("writer")
        }
    )

    assert workflow is not None
    print("✓ Research workflow created")


if __name__ == "__main__":
    print("="*60)
    print("LangGraph Workflow Infrastructure Test")
    print("="*60)

    try:
        test_imports()
        test_orchestrator_creation()
        test_workflow_structure()

        print("\n" + "="*60)
        print("✓ ALL TESTS PASSED")
        print("="*60)
        print("\nWorkflow infrastructure is ready to use!")
        print("\nNext steps:")
        print("1. Set up API keys in .env (OPENAI_API_KEY or ANTHROPIC_API_KEY)")
        print("2. Configure Supabase for shared memory (optional)")
        print("3. Run examples/langgraph_demo.py for full demonstrations")

    except Exception as e:
        print("\n" + "="*60)
        print("✗ TEST FAILED")
        print("="*60)
        print(f"\nError: {e}")
        raise

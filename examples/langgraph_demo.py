"""
LangGraph Multi-Agent Workflow Demo

Demonstrates how agents collaborate using:
1. StateGraph for workflow orchestration
2. Shared semantic memory for learning
3. Quality gates with automatic retry
4. Multiple collaboration patterns

Run this to see agents working together for remarkable results.
"""

import os
from typing import Dict, Any

# Set up environment (use actual values from .env in production)
os.environ.setdefault("OPENAI_API_KEY", "your-key-here")
os.environ.setdefault("ANTHROPIC_API_KEY", "your-key-here")

from agent_factory.core.agent_factory import AgentFactory
from agent_factory.workflows.graph_orchestrator import create_research_workflow
from agent_factory.workflows.collaboration_patterns import (
    create_parallel_research,
    create_consensus_workflow,
    create_supervisor_workflow
)
from agent_factory.workflows.shared_memory import SharedAgentMemory


def demo_research_workflow():
    """
    Demo 1: Research Workflow with Quality Gates

    Shows how agents pass context to each other:
    Planner → Researcher → Analyzer → Writer

    Quality gate ensures good results or triggers retry.
    """
    print("\n" + "="*60)
    print("DEMO 1: Research Workflow with Quality Gates")
    print("="*60 + "\n")

    # Create agents
    factory = AgentFactory()

    planner = factory.create_agent(
        role="Research Planner",
        goal="Decide what to research about the query",
        backstory="Expert at breaking down complex questions",
        verbose=True
    )

    researcher = factory.create_agent(
        role="Researcher",
        goal="Find accurate information",
        backstory="Skilled at finding reliable sources",
        verbose=True
    )

    analyzer = factory.create_agent(
        role="Quality Analyzer",
        goal="Evaluate research quality",
        backstory="Critical thinker who ensures accuracy",
        verbose=True
    )

    writer = factory.create_agent(
        role="Writer",
        goal="Create clear, comprehensive answers",
        backstory="Technical writer who explains complex topics simply",
        verbose=True
    )

    # Create workflow
    workflow = create_research_workflow(
        agents={
            "planner": planner,
            "researcher": researcher,
            "analyzer": analyzer,
            "writer": writer
        },
        quality_threshold=0.7,
        max_retries=2,
        verbose=True
    )

    # Execute workflow
    result = workflow.invoke({
        "query": "What is a PLC and what are the main manufacturers?",
        "context": [],
        "findings": {},
        "errors": [],
        "retry_count": 0,
        "quality_score": 0.0,
        "current_step": "",
        "final_answer": "",
        "metadata": {}
    })

    print("\n" + "-"*60)
    print("FINAL ANSWER:")
    print("-"*60)
    print(result["final_answer"])
    print("\nQuality Score:", result["quality_score"])
    print("Retries:", result["retry_count"])


def demo_parallel_research():
    """
    Demo 2: Parallel Research (Fan-Out/Fan-In)

    Multiple research agents work simultaneously on
    different aspects. Synthesis agent combines findings.

    3x faster than sequential research.
    """
    print("\n" + "="*60)
    print("DEMO 2: Parallel Research (Fan-Out/Fan-In)")
    print("="*60 + "\n")

    factory = AgentFactory()

    # Create 3 specialized researchers
    researcher1 = factory.create_agent(
        role="Hardware Researcher",
        goal="Find information about PLC hardware",
        backstory="Expert in industrial hardware",
        verbose=True
    )

    researcher2 = factory.create_agent(
        role="Software Researcher",
        goal="Find information about PLC programming",
        backstory="Expert in PLC software and programming",
        verbose=True
    )

    researcher3 = factory.create_agent(
        role="Applications Researcher",
        goal="Find information about PLC applications",
        backstory="Expert in industrial automation applications",
        verbose=True
    )

    synthesizer = factory.create_agent(
        role="Synthesis Expert",
        goal="Combine research findings into unified answer",
        backstory="Expert at synthesizing information from multiple sources",
        verbose=True
    )

    # Create parallel workflow
    # Note: This returns a coroutine, needs async execution
    print("Note: Parallel workflow requires async execution")
    print("See examples/async_demo.py for full implementation")


def demo_consensus_building():
    """
    Demo 3: Consensus Building

    Multiple agents generate candidate answers.
    Judge agent picks the best one.

    Ensures high-quality answers through competition.
    """
    print("\n" + "="*60)
    print("DEMO 3: Consensus Building")
    print("="*60 + "\n")

    factory = AgentFactory()

    # Create 3 solver agents
    solver1 = factory.create_agent(
        role="Technical Expert",
        goal="Provide technically accurate answers",
        backstory="Deep technical knowledge, sometimes too detailed",
        verbose=True
    )

    solver2 = factory.create_agent(
        role="Practical Expert",
        goal="Provide practical, actionable answers",
        backstory="Focuses on real-world applications",
        verbose=True
    )

    solver3 = factory.create_agent(
        role="Teaching Expert",
        goal="Provide clear, educational answers",
        backstory="Excellent at explaining complex topics simply",
        verbose=True
    )

    judge = factory.create_agent(
        role="Judge",
        goal="Pick the best answer from candidates",
        backstory="Expert evaluator of answer quality",
        verbose=True
    )

    # Create consensus workflow
    workflow = create_consensus_workflow(
        agents={
            "solvers": [solver1, solver2, solver3],
            "judge": judge
        },
        consensus_method="judge",
        verbose=True
    )

    # Execute workflow
    result = workflow.invoke({
        "query": "What is the best PLC for beginners?",
        "candidate_answers": [],
        "scores": {},
        "final_answer": "",
        "consensus_method": "judge"
    })

    print("\n" + "-"*60)
    print("FINAL ANSWER (chosen by judge):")
    print("-"*60)
    print(result["final_answer"])


def demo_shared_memory():
    """
    Demo 4: Shared Semantic Memory

    Agents store discoveries that other agents can
    later retrieve via semantic search.

    Enables learning from past work.
    """
    print("\n" + "="*60)
    print("DEMO 4: Shared Semantic Memory")
    print("="*60 + "\n")

    # Note: Requires Supabase setup
    print("Note: This requires Supabase pgvector setup")
    print("See: docs/database/supabase_complete_schema.sql")
    print("\nIf Supabase is configured:")

    try:
        memory = SharedAgentMemory(embedding_provider="openai")

        # Store some discoveries
        print("\n1. Storing discoveries...")
        memory.store(
            content="Allen-Bradley is the most popular PLC brand in North America",
            agent_name="ResearchAgent",
            metadata={"topic": "plc_brands", "quality": 0.9}
        )

        memory.store(
            content="Siemens PLCs are common in Europe and use STEP 7 programming",
            agent_name="ResearchAgent",
            metadata={"topic": "plc_brands", "quality": 0.9}
        )

        memory.store(
            content="PLC scan cycle typically runs at 10-50ms intervals",
            agent_name="ResearchAgent",
            metadata={"topic": "plc_basics", "quality": 0.95}
        )

        # Retrieve relevant discoveries
        print("\n2. Retrieving relevant discoveries...")
        discoveries = memory.retrieve(
            query="What are popular PLC manufacturers?",
            limit=3
        )

        print(f"\nFound {len(discoveries)} relevant discoveries:")
        for i, d in enumerate(discoveries, 1):
            print(f"\n{i}. {d['agent_name']} ({d['created_at'][:10]}):")
            print(f"   {d['content'][:100]}...")

        # Get stats
        stats = memory.get_stats()
        print(f"\nMemory Stats:")
        print(f"  Total memories: {stats['total']}")
        print(f"  Agents: {', '.join(stats['by_agent'].keys())}")

    except Exception as e:
        print(f"\nShared memory not available: {e}")
        print("Configure Supabase to enable this feature")


def demo_supervisor_delegation():
    """
    Demo 5: Supervisor Delegation

    Supervisor analyzes query and delegates to
    appropriate specialist teams.

    Enables complex multi-stage workflows.
    """
    print("\n" + "="*60)
    print("DEMO 5: Supervisor Delegation")
    print("="*60 + "\n")

    factory = AgentFactory()

    supervisor = factory.create_agent(
        role="Workflow Supervisor",
        goal="Analyze queries and delegate to appropriate teams",
        backstory="Expert coordinator who knows which specialists to use",
        verbose=True
    )

    research_team = factory.create_agent(
        role="Research Team",
        goal="Find information on any topic",
        backstory="Skilled researchers",
        verbose=True
    )

    analysis_team = factory.create_agent(
        role="Analysis Team",
        goal="Analyze data and provide insights",
        backstory="Data analysts and critical thinkers",
        verbose=True
    )

    coding_team = factory.create_agent(
        role="Coding Team",
        goal="Write and explain code",
        backstory="Software engineers and programmers",
        verbose=True
    )

    # Create supervisor workflow
    workflow = create_supervisor_workflow(
        agents={
            "supervisor": supervisor,
            "teams": {
                "research": research_team,
                "analysis": analysis_team,
                "coding": coding_team
            }
        },
        verbose=True
    )

    # Execute workflow
    result = workflow.invoke({
        "query": "Find PLC programming examples and analyze common patterns",
        "supervisor_decision": {},
        "delegated_results": [],
        "final_answer": ""
    })

    print("\n" + "-"*60)
    print("DELEGATED RESULTS:")
    print("-"*60)
    print(result["final_answer"])


if __name__ == "__main__":
    print("\n" + "="*60)
    print("LangGraph Multi-Agent Workflow Demos")
    print("="*60)
    print("\nThese demos show how agents collaborate for remarkable results.")
    print("\nNote: Some demos require API keys and Supabase setup.")
    print("Configure .env before running.")

    # Run demos
    # Uncomment to run individual demos:

    # demo_research_workflow()
    # demo_parallel_research()
    # demo_consensus_building()
    # demo_shared_memory()
    # demo_supervisor_delegation()

    print("\n" + "="*60)
    print("Demos Complete!")
    print("="*60)
    print("\nUncomment specific demos in __main__ to run them.")
    print("Start with demo_research_workflow() for a complete example.")

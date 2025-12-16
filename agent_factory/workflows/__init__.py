"""
LangGraph Workflows - Advanced Multi-Agent Collaboration

This module provides LangGraph-based workflows for sophisticated
agent collaboration patterns including:
- Sequential pipelines (research → analyze → write)
- Parallel execution (multiple agents working simultaneously)
- Consensus building (multiple agents vote on best answer)
- Supervisor delegation (coordinator manages worker agents)
"""

from .graph_orchestrator import GraphOrchestrator, create_research_workflow
from .collaboration_patterns import (
    create_parallel_research,
    create_consensus_workflow,
    create_supervisor_workflow
)
from .shared_memory import SharedAgentMemory

__all__ = [
    "GraphOrchestrator",
    "create_research_workflow",
    "create_parallel_research",
    "create_consensus_workflow",
    "create_supervisor_workflow",
    "SharedAgentMemory"
]

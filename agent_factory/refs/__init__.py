"""
Project Twin (refs) - Digital Twin System for Codebase

This module provides a digital twin representation of the project:
- ProjectTwin: Main twin class that mirrors the codebase
- CodeAnalyzer: AST-based Python code analysis
- KnowledgeGraph: Dependency relationship graph
- TwinAgent: LLM agent interface to query the twin

Usage:
    from agent_factory.refs import ProjectTwin, TwinAgent

    twin = ProjectTwin(project_root=Path.cwd())
    twin.sync(include_patterns=["*.py"])

    twin_agent = TwinAgent(twin, llm)
    result = twin_agent.query("Where is AgentFactory defined?")
"""

from .project_twin import FileNode, ProjectTwin
from .code_analyzer import CodeAnalyzer
from .knowledge_graph import KnowledgeGraph
from .twin_agent import TwinAgent

__all__ = [
    "FileNode",
    "ProjectTwin",
    "CodeAnalyzer",
    "KnowledgeGraph",
    "TwinAgent",
]

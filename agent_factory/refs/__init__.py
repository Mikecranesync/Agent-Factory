"""
Project Twin - Codebase Understanding System

This module provides codebase parsing, indexing, and querying capabilities
to help agents understand project structure, dependencies, and patterns.

Phase 6 Components:
- parser: AST-based Python code parser
- indexer: Searchable code index with fuzzy matching
- query: Natural language query interface
- patterns: Pattern detection and code suggestions
"""

from agent_factory.refs.parser import (
    CodeElement,
    PythonParser,
)
from agent_factory.refs.indexer import (
    ProjectIndex,
)
from agent_factory.refs.query import (
    QueryResult,
    QueryEngine,
)
from agent_factory.refs.patterns import (
    CodePattern,
    PatternDetector,
)

__all__ = [
    # Parser
    "CodeElement",
    "PythonParser",
    # Indexer
    "ProjectIndex",
    # Query
    "QueryResult",
    "QueryEngine",
    # Patterns
    "CodePattern",
    "PatternDetector",
]

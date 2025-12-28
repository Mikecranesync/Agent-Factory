"""
RIVET Pro RAG Layer

Retrieval-Augmented Generation (RAG) infrastructure for knowledge base queries.

Components:
- config: Collection definitions and search configuration
- retriever: Knowledge base search and coverage estimation
- filters: Supabase filter building from RivetIntent

Usage:
    from agent_factory.rivet_pro.rag import search_docs, estimate_coverage
    
    docs = search_docs(intent, agent_id="siemens", top_k=8)
    coverage = estimate_coverage(intent)
"""

from agent_factory.rivet_pro.rag.retriever import search_docs, estimate_coverage
from agent_factory.rivet_pro.rag.config import (
    RAGConfig,
    RetrievedDoc,
    COLLECTION_NAME,
    DEFAULT_TOP_K,
    COVERAGE_THRESHOLDS
)

__all__ = [
    "search_docs",
    "estimate_coverage",
    "RAGConfig",
    "RetrievedDoc",
    "COLLECTION_NAME",
    "DEFAULT_TOP_K",
    "COVERAGE_THRESHOLDS"
]

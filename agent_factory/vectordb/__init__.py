"""
Vector Database Integration for Knowledge Atoms

Provides Supabase + pgvector integration for storing and retrieving Knowledge Atoms.
Cost-effective alternative to Pinecone ($0-25/month vs $50-500/month).
"""

from agent_factory.vectordb.supabase_vector_config import (
    SupabaseVectorConfig,
    SUPABASE_VECTOR_CONFIG,
    VectorDBProvider,
)
from agent_factory.vectordb.supabase_vector_client import (
    SupabaseVectorClient,
    SupabaseConnectionError,
)
from agent_factory.vectordb.knowledge_atom_store import (
    KnowledgeAtomStore,
    InsertionError,
    QueryError,
)

__all__ = [
    "SupabaseVectorConfig",
    "SUPABASE_VECTOR_CONFIG",
    "VectorDBProvider",
    "SupabaseVectorClient",
    "SupabaseConnectionError",
    "KnowledgeAtomStore",
    "InsertionError",
    "QueryError",
]

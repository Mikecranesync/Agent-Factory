"""
RAG Retriever for RIVET Pro

Knowledge base search and coverage estimation.

Phase 2/8 of RIVET Pro Multi-Agent Backend.
"""

from typing import List, Optional, Dict, Any
import logging

from agent_factory.rivet_pro.models import RivetIntent, KBCoverage
from agent_factory.rivet_pro.rag.config import (
    RetrievedDoc,
    RAGConfig,
    AGENT_CONFIGS,
    COLLECTION_NAME,
    COVERAGE_THRESHOLDS,
    DEFAULT_TOP_K
)
from agent_factory.rivet_pro.rag.filters import (
    build_metadata_filter,
    build_atom_type_filter,
    combine_filters,
    extract_search_keywords
)

logger = logging.getLogger(__name__)


def get_supabase_client():
    """Get Supabase client for knowledge base queries."""
    try:
        from agent_factory.rivet_pro.database import RIVETProDatabase
        db = RIVETProDatabase()
        return db.client
    except Exception as e:
        logger.error(f"Failed to get Supabase client: {e}")
        return None


def search_docs(
    intent: RivetIntent,
    agent_id: str = "generic_plc",
    top_k: int = DEFAULT_TOP_K,
    config: Optional[RAGConfig] = None
) -> List[RetrievedDoc]:
    """
    Search knowledge base using RivetIntent.
    
    Args:
        intent: Classified user intent
        agent_id: Which SME agent is requesting
        top_k: Number of documents to retrieve
        config: Optional custom RAG configuration
    
    Returns:
        List of retrieved documents
    """
    if config is None:
        config = AGENT_CONFIGS.get(agent_id, RAGConfig())

    if config.vendor_filter is None and agent_id in AGENT_CONFIGS:
        config.vendor_filter = AGENT_CONFIGS[agent_id].vendor_filter

    client = get_supabase_client()
    if not client:
        logger.warning("No database client available")
        return []

    try:
        metadata_filter = build_metadata_filter(intent)

        if config.vendor_filter:
            metadata_filter["vendor"] = {"$eq": config.vendor_filter}
        if config.equipment_filter:
            metadata_filter["equipment_filter"] = {"$eq": config.equipment_filter}

        atom_type_filter = build_atom_type_filter(config.atom_type_filter)
        full_filter = combine_filters(metadata_filter, atom_type_filter)

        if config.use_hybrid_search and intent.raw_summary:
            docs = _hybrid_search(client, intent, full_filter, top_k, config)
        else:
            docs = _keyword_search(client, intent, full_filter, top_k)

        logger.info(f"Retrieved {len(docs)} documents for agent '{agent_id}'")
        return docs

    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        return []


def estimate_coverage(
    intent: RivetIntent,
    agent_id: str = "generic_plc"
) -> KBCoverage:
    """
    Estimate knowledge base coverage.
    
    Args:
        intent: Classified user intent
        agent_id: Which SME agent is requesting
    
    Returns:
        KBCoverage enum (STRONG, THIN, NONE)
    """
    docs = search_docs(intent, agent_id=agent_id, top_k=20)
    doc_count = len(docs)

    if doc_count >= COVERAGE_THRESHOLDS["strong"]:
        return KBCoverage.STRONG
    elif doc_count >= COVERAGE_THRESHOLDS["thin"]:
        return KBCoverage.THIN
    else:
        return KBCoverage.NONE


def _hybrid_search(
    client: Any,
    intent: RivetIntent,
    metadata_filter: Dict[str, Any],
    top_k: int,
    config: RAGConfig
) -> List[RetrievedDoc]:
    """Hybrid semantic + keyword search."""
    query_text = intent.raw_summary or ""
    keywords = extract_search_keywords(intent)
    keyword_query = " ".join(keywords) if keywords else query_text

    try:
        response = client.rpc(
            "match_knowledge_atoms",
            {
                "query_embedding": None,
                "query_text": keyword_query,
                "match_threshold": config.min_similarity,
                "match_count": top_k,
                "filter": metadata_filter
            }
        ).execute()

        docs = []
        for row in response.data[:top_k]:
            try:
                doc = _parse_db_row(row)
                docs.append(doc)
            except Exception as e:
                logger.warning(f"Failed to parse document: {e}")
                continue

        return docs

    except Exception as e:
        logger.warning(f"Hybrid search failed, falling back: {e}")
        return _keyword_search(client, intent, metadata_filter, top_k)


def _keyword_search(
    client: Any,
    intent: RivetIntent,
    metadata_filter: Dict[str, Any],
    top_k: int
) -> List[RetrievedDoc]:
    """Keyword-only search fallback."""
    keywords = extract_search_keywords(intent)

    try:
        query = client.from_(COLLECTION_NAME).select("*")

        for key, condition in metadata_filter.items():
            if "$eq" in condition:
                query = query.eq(key, condition["$eq"])
            elif "$in" in condition:
                query = query.in_(key, condition["$in"])
            elif "$contains" in condition:
                query = query.contains(key, condition["$contains"])

        if keywords and len(keywords) > 0:
            search_term = " | ".join(keywords)
            query = query.textSearch("keywords", search_term)

        response = query.limit(top_k).execute()

        docs = []
        for row in response.data:
            try:
                doc = _parse_db_row(row)
                docs.append(doc)
            except Exception as e:
                logger.warning(f"Failed to parse document: {e}")
                continue

        return docs

    except Exception as e:
        logger.error(f"Keyword search failed: {e}")
        return []


def _parse_db_row(row: Dict[str, Any]) -> RetrievedDoc:
    """Parse database row into RetrievedDoc model."""
    return RetrievedDoc(
        atom_id=row.get("atom_id", ""),
        title=row.get("title", ""),
        summary=row.get("summary", ""),
        content=row.get("content", ""),
        atom_type=row.get("type", "concept"),
        vendor=row.get("vendor"),
        equipment_type=row.get("equipment_type"),
        similarity_score=row.get("similarity", 0.0),
        keywords=row.get("keywords", []),
        source=row.get("source"),
        page_number=row.get("page_number"),
        difficulty=row.get("difficulty"),
        safety_level=row.get("safety_level"),
        fault_codes=row.get("fault_codes", []),
        models=row.get("models", [])
    )

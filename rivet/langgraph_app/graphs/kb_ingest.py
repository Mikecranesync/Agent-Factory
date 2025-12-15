"""
KB Ingestion Graph - Main workflow for knowledge base ingestion

Flow: Discovery → Downloader → Parser → Critic → Indexer
"""

import logging
from langgraph.graph import StateGraph, END
from langgraph_app.state import RivetState
from langgraph_app.nodes import (
    discovery_node,
    downloader_node,
    parser_node,
    critic_node,
    indexer_node
)

logger = logging.getLogger(__name__)


def build_kb_ingest_graph():
    """
    Build knowledge base ingestion workflow

    Nodes:
    - discovery: Find source document URL
    - downloader: Download and extract text
    - parser: Extract knowledge atoms using LLM
    - critic: Validate extracted atoms
    - indexer: Store atoms in database with embeddings

    Returns:
        Compiled LangGraph workflow
    """
    logger.info("Building KB ingestion graph")

    # Create graph
    graph = StateGraph(RivetState)

    # Add nodes
    graph.add_node("discovery", discovery_node)
    graph.add_node("downloader", downloader_node)
    graph.add_node("parser", parser_node)
    graph.add_node("critic", critic_node)
    graph.add_node("indexer", indexer_node)

    # Define flow
    graph.set_entry_point("discovery")
    graph.add_edge("discovery", "downloader")
    graph.add_edge("downloader", "parser")
    graph.add_edge("parser", "critic")

    # Conditional edge from critic
    def should_index(state):
        """Check if we should proceed to indexing"""
        if state.errors:
            logger.warning(f"Job {state.job_id}: Skipping indexing due to errors")
            return END
        return "indexer"

    graph.add_conditional_edges(
        "critic",
        should_index,
        {
            "indexer": "indexer",
            END: END
        }
    )

    graph.add_edge("indexer", END)

    # Compile and return
    compiled_graph = graph.compile()
    logger.info("KB ingestion graph compiled successfully")

    return compiled_graph

"""
KB Ingestion Graph - Main LangGraph workflow
"""

from langgraph.graph import StateGraph, END
from langgraph_app.state import RivetState
from langgraph_app.nodes import (
    discovery_node,
    downloader_node,
    parser_node,
    critic_node,
    indexer_node
)


def should_continue_after_critic(state: RivetState) -> str:
    """
    Decide whether to index or stop after critique

    Args:
        state: Current state

    Returns:
        Next node name or END
    """
    if state.errors:
        return END
    if not state.atoms:
        return END
    return "indexer"


def build_kb_ingest_graph():
    """
    Build the KB ingestion LangGraph workflow

    Pipeline:
    1. Discovery: Find source URL
    2. Downloader: Fetch document
    3. Parser: Extract structured atoms via LLM
    4. Critic: Validate atoms
    5. Indexer: Store in Postgres + pgvector (if valid)

    Returns:
        Compiled graph
    """
    graph = StateGraph(RivetState)

    # Add nodes
    graph.add_node("discovery", discovery_node)
    graph.add_node("downloader", downloader_node)
    graph.add_node("parser", parser_node)
    graph.add_node("critic", critic_node)
    graph.add_node("indexer", indexer_node)

    # Define edges
    graph.set_entry_point("discovery")
    graph.add_edge("discovery", "downloader")
    graph.add_edge("downloader", "parser")
    graph.add_edge("parser", "critic")

    # Conditional edge: only index if validation passed
    graph.add_conditional_edges(
        "critic",
        should_continue_after_critic,
        {
            "indexer": "indexer",
            END: END
        }
    )

    graph.add_edge("indexer", END)

    return graph.compile()

"""
Discovery node: Find source documents to process
"""

import logging
from langgraph_app.state import RivetState

logger = logging.getLogger(__name__)


def discovery_node(state: RivetState) -> RivetState:
    """
    Discover source documents for ingestion

    If source_url is already provided, pass through.
    Otherwise, fetch next URL from database or queue.

    Args:
        state: Current graph state

    Returns:
        Updated state with source_url populated
    """
    state.logs.append("Starting discovery")

    # If URL already provided, just validate and pass through
    if state.source_url:
        logger.info(f"[{state.job_id}] Source URL already provided: {state.source_url}")
        state.logs.append(f"Using provided URL: {state.source_url}")
        return state

    # TODO: In production, query Postgres sources table or similar
    # For now, this will be handled by scheduler pushing to Redis

    logger.warning(f"[{state.job_id}] No source URL provided")
    state.errors.append("No source URL to process")

    return state

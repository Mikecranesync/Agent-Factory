"""
Discovery Node - Find source documents to ingest

Retrieves URLs from queue or database for processing.
"""

import logging
from typing import Dict, Any
from langgraph_app.state import RivetState

logger = logging.getLogger(__name__)


def discovery_node(state: RivetState) -> Dict[str, Any]:
    """
    Discover source document URLs for ingestion

    If source_url is already in state, validates and passes through.
    Otherwise, retrieves next URL from sources queue/database.

    Args:
        state: Current workflow state

    Returns:
        Updated state with source_url populated
    """
    logger.info(f"[{state.job_id}] Discovery node started")

    # If URL already provided, validate and proceed
    if state.source_url:
        logger.info(f"[{state.job_id}] Source URL provided: {state.source_url}")
        state.logs.append(f"Using provided URL: {state.source_url}")

        # Basic URL validation
        if not state.source_url.startswith(("http://", "https://")):
            state.errors.append(f"Invalid URL format: {state.source_url}")
            logger.error(f"[{state.job_id}] Invalid URL format")
            return state.dict()

        return state.dict()

    # Otherwise, discover from sources database/queue
    # TODO: Implement database lookup for pending sources
    # For now, use placeholder
    logger.warning(f"[{state.job_id}] No source URL provided and discovery not implemented")
    state.errors.append("No source URL provided")

    return state.dict()

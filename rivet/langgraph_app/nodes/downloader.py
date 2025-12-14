"""
Downloader node: Fetch and extract document content
"""

import logging
import requests
from pathlib import Path
from typing import Optional
from langgraph_app.state import RivetState

logger = logging.getLogger(__name__)


def download_document(url: str, timeout: int = 30) -> tuple[bytes, str]:
    """
    Download document from URL

    Args:
        url: Document URL
        timeout: Request timeout in seconds

    Returns:
        Tuple of (content_bytes, content_type)
    """
    logger.info(f"Downloading: {url}")

    response = requests.get(url, timeout=timeout, allow_redirects=True)
    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "").lower()

    return response.content, content_type


def extract_text_from_pdf(content: bytes) -> str:
    """
    Extract text from PDF content

    TODO: Implement using PyPDF2 or pdfplumber
    For V1, returns placeholder
    """
    # Placeholder - in production, use proper PDF parser
    logger.warning("PDF parsing not yet implemented - using placeholder")
    return "[PDF Content - Parser Not Implemented Yet]"


def extract_text_from_html(content: bytes) -> str:
    """
    Extract text from HTML content

    TODO: Implement using BeautifulSoup or similar
    For V1, returns placeholder
    """
    # Placeholder - in production, use proper HTML parser
    try:
        return content.decode("utf-8")
    except:
        return content.decode("latin-1")


def downloader_node(state: RivetState) -> RivetState:
    """
    Download document and extract text

    Args:
        state: Current graph state

    Returns:
        Updated state with raw_document and metadata populated
    """
    state.logs.append("Starting download")

    if not state.source_url:
        error_msg = "No source URL to download"
        logger.error(f"[{state.job_id}] {error_msg}")
        state.errors.append(error_msg)
        return state

    try:
        # Download document
        content, content_type = download_document(state.source_url)

        # Detect document type
        if "pdf" in content_type or state.source_url.endswith(".pdf"):
            state.source_type = "pdf"
            text = extract_text_from_pdf(content)
        elif "html" in content_type or state.source_url.endswith(".html"):
            state.source_type = "html"
            text = extract_text_from_html(content)
        else:
            # Try as plain text
            state.source_type = "text"
            text = content.decode("utf-8", errors="ignore")

        state.raw_document = text
        state.metadata["source_url"] = state.source_url
        state.metadata["source_type"] = state.source_type
        state.metadata["content_length"] = len(text)

        logger.info(
            f"[{state.job_id}] Downloaded {state.source_type}: "
            f"{len(text)} chars from {state.source_url}"
        )
        state.logs.append(f"Downloaded {len(text)} chars ({state.source_type})")

    except Exception as e:
        error_msg = f"Download failed: {str(e)}"
        logger.error(f"[{state.job_id}] {error_msg}")
        state.errors.append(error_msg)

    return state

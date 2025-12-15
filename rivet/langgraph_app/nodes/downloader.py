"""
Downloader Node - Fetch and extract document content

Downloads PDF/HTML documents and converts to plain text.
"""

import io
import logging
import requests
from typing import Dict, Any
from langgraph_app.state import RivetState

logger = logging.getLogger(__name__)

# PDF libraries - import with fallbacks
try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False
    logger.warning("PyPDF2 not available")

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    logger.warning("pdfplumber not available")

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    logger.warning("BeautifulSoup not available")


def downloader_node(state: RivetState) -> Dict[str, Any]:
    """
    Download document from URL and extract text

    Supports:
    - PDF files (via PyPDF2 or similar)
    - HTML pages (via BeautifulSoup)
    - Plain text files

    Args:
        state: Current workflow state

    Returns:
        Updated state with raw_document and metadata
    """
    logger.info(f"[{state.job_id}] Downloader node started for: {state.source_url}")

    try:
        # Download document
        response = requests.get(state.source_url, timeout=30)
        response.raise_for_status()

        content_type = response.headers.get("content-type", "").lower()
        logger.info(f"[{state.job_id}] Downloaded {len(response.content)} bytes, type: {content_type}")

        # Extract text based on content type
        if "pdf" in content_type or state.source_url.endswith(".pdf"):
            raw_text = extract_pdf_text(response.content)
        elif "html" in content_type:
            raw_text = extract_html_text(response.text)
        else:
            raw_text = response.text

        state.raw_document = raw_text
        state.metadata.update({
            "content_type": content_type,
            "content_length": len(response.content),
            "extracted_length": len(raw_text),
        })

        state.logs.append(f"Downloaded and extracted {len(raw_text)} chars")
        logger.info(f"[{state.job_id}] Extraction complete: {len(raw_text)} chars")

    except requests.RequestException as e:
        error_msg = f"Download failed: {str(e)}"
        state.errors.append(error_msg)
        logger.error(f"[{state.job_id}] {error_msg}")

    except Exception as e:
        error_msg = f"Text extraction failed: {str(e)}"
        state.errors.append(error_msg)
        logger.error(f"[{state.job_id}] {error_msg}")

    return state.dict()


def extract_pdf_text(pdf_bytes: bytes) -> str:
    """
    Extract text from PDF bytes using PyPDF2 or pdfplumber

    Tries PyPDF2 first (faster), falls back to pdfplumber (better for complex PDFs)
    """
    text_parts = []

    # Try PyPDF2 first (faster for simple PDFs)
    if PYPDF2_AVAILABLE:
        try:
            pdf_file = io.BytesIO(pdf_bytes)
            reader = PyPDF2.PdfReader(pdf_file)

            logger.info(f"PDF has {len(reader.pages)} pages")

            for page_num, page in enumerate(reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(f"--- Page {page_num + 1} ---\n{page_text}")
                except Exception as e:
                    logger.warning(f"PyPDF2 failed on page {page_num + 1}: {e}")

            if text_parts:
                result = "\n\n".join(text_parts)
                logger.info(f"PyPDF2 extracted {len(result)} chars from {len(reader.pages)} pages")
                return result

        except Exception as e:
            logger.warning(f"PyPDF2 extraction failed: {e}")

    # Fallback to pdfplumber (better for complex layouts)
    if PDFPLUMBER_AVAILABLE:
        try:
            pdf_file = io.BytesIO(pdf_bytes)
            with pdfplumber.open(pdf_file) as pdf:
                logger.info(f"pdfplumber: PDF has {len(pdf.pages)} pages")

                for page_num, page in enumerate(pdf.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(f"--- Page {page_num + 1} ---\n{page_text}")
                    except Exception as e:
                        logger.warning(f"pdfplumber failed on page {page_num + 1}: {e}")

                if text_parts:
                    result = "\n\n".join(text_parts)
                    logger.info(f"pdfplumber extracted {len(result)} chars from {len(pdf.pages)} pages")
                    return result

        except Exception as e:
            logger.warning(f"pdfplumber extraction failed: {e}")

    # No extraction worked
    if not PYPDF2_AVAILABLE and not PDFPLUMBER_AVAILABLE:
        logger.error("No PDF libraries available - install PyPDF2 or pdfplumber")
        return f"[ERROR: No PDF libraries available - {len(pdf_bytes)} bytes]"

    logger.warning(f"PDF extraction returned no text from {len(pdf_bytes)} byte document")
    return f"[PDF extraction failed - {len(pdf_bytes)} bytes, no text extracted]"


def extract_html_text(html_content: str) -> str:
    """
    Extract text from HTML content using BeautifulSoup

    Removes scripts, styles, and extracts meaningful text.
    """
    if BS4_AVAILABLE:
        try:
            soup = BeautifulSoup(html_content, 'lxml')

            # Remove script and style elements
            for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                element.decompose()

            # Get text with proper spacing
            text = soup.get_text(separator='\n', strip=True)

            # Clean up excessive whitespace
            import re
            text = re.sub(r'\n{3,}', '\n\n', text)
            text = re.sub(r' {2,}', ' ', text)

            logger.info(f"BeautifulSoup extracted {len(text)} chars from HTML")
            return text

        except Exception as e:
            logger.warning(f"BeautifulSoup extraction failed: {e}")

    # Fallback - basic regex tag removal
    import re
    text = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()

    logger.info(f"Regex extracted {len(text)} chars from HTML")
    return text

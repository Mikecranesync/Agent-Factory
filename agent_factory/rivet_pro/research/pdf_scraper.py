"""
Manufacturer documentation scraper for PDFs.

Retrieves technical documentation from manufacturer websites when Route C (No KB Coverage) is triggered.
"""

import logging
import requests
import hashlib
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from urllib.parse import urlparse
import PyPDF2
import io

logger = logging.getLogger(__name__)


@dataclass
class PDFResult:
    """Result from PDF document extraction."""

    url: str
    title: str
    content: str  # Extracted text from PDF
    metadata: Dict[str, Any] = field(default_factory=dict)
    source_type: str = "manufacturer_pdf"


class PDFScraper:
    """
    Scrapes manufacturer documentation PDFs.

    Handles:
    - PDF download from URL
    - Text extraction via PyPDF2
    - Metadata extraction (title, author, page count)
    - Content chunking for large documents
    """

    def __init__(self, max_retries: int = 3, max_pages: int = 100):
        """
        Initialize PDF scraper.

        Args:
            max_retries: Maximum number of download retries
            max_pages: Maximum number of pages to extract (prevents OOM on huge docs)
        """
        self.max_retries = max_retries
        self.max_pages = max_pages
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "AgentFactory/1.0 (Industrial Automation Research Bot)"
        })

    def scrape(self, url: str) -> Optional[PDFResult]:
        """
        Scrape a single PDF document.

        Args:
            url: URL to PDF file

        Returns:
            PDFResult object or None if scraping failed
        """
        try:
            # Download PDF
            logger.info(f"Downloading PDF from {url}")
            pdf_bytes = self._download_pdf(url)
            if not pdf_bytes:
                logger.error(f"Failed to download PDF from {url}")
                return None

            # Extract text and metadata
            text, metadata = self._extract_pdf_content(pdf_bytes)
            if not text:
                logger.error(f"Failed to extract text from PDF: {url}")
                return None

            # Generate title from URL if not in metadata
            title = metadata.get("title") or self._generate_title_from_url(url)

            result = PDFResult(
                url=url,
                title=title,
                content=text,
                metadata=metadata
            )

            logger.info(f"Successfully scraped PDF: {title} ({metadata.get('pages', 0)} pages)")
            return result

        except Exception as e:
            logger.error(f"PDF scraping failed for {url}: {e}", exc_info=True)
            return None

    def scrape_batch(self, urls: List[str]) -> List[PDFResult]:
        """
        Scrape multiple PDF documents.

        Args:
            urls: List of PDF URLs

        Returns:
            List of successfully scraped PDFResult objects
        """
        results = []

        for url in urls:
            result = self.scrape(url)
            if result:
                results.append(result)

        logger.info(f"Batch scraping completed: {len(results)}/{len(urls)} PDFs successful")
        return results

    def _download_pdf(self, url: str) -> Optional[bytes]:
        """
        Download PDF from URL.

        Args:
            url: URL to PDF file

        Returns:
            PDF bytes or None if download failed
        """
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()

                # Verify content type is PDF
                content_type = response.headers.get("Content-Type", "")
                if "pdf" not in content_type.lower():
                    logger.warning(f"URL does not appear to be a PDF: {content_type}")

                return response.content

            except requests.RequestException as e:
                logger.warning(f"Download attempt {attempt + 1}/{self.max_retries} failed: {e}")
                if attempt < self.max_retries - 1:
                    continue

        return None

    def _extract_pdf_content(self, pdf_bytes: bytes) -> tuple[str, Dict[str, Any]]:
        """
        Extract text and metadata from PDF bytes.

        Args:
            pdf_bytes: PDF file content

        Returns:
            Tuple of (extracted_text, metadata_dict)
        """
        try:
            pdf_file = io.BytesIO(pdf_bytes)
            pdf_reader = PyPDF2.PdfReader(pdf_file)

            # Extract metadata
            metadata = {
                "pages": len(pdf_reader.pages),
                "title": pdf_reader.metadata.get("/Title", "") if pdf_reader.metadata else "",
                "author": pdf_reader.metadata.get("/Author", "") if pdf_reader.metadata else "",
                "subject": pdf_reader.metadata.get("/Subject", "") if pdf_reader.metadata else "",
            }

            # Extract text from pages
            text_parts = []
            pages_to_extract = min(len(pdf_reader.pages), self.max_pages)

            for i in range(pages_to_extract):
                try:
                    page = pdf_reader.pages[i]
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {i}: {e}")
                    continue

            # Combine all text
            full_text = "\n".join(text_parts)

            # Truncate if too long (prevent OOM)
            max_chars = 100000  # ~100KB of text
            if len(full_text) > max_chars:
                logger.warning(f"PDF text truncated from {len(full_text)} to {max_chars} chars")
                full_text = full_text[:max_chars]
                metadata["truncated"] = True

            return full_text, metadata

        except Exception as e:
            logger.error(f"PDF extraction failed: {e}", exc_info=True)
            return "", {}

    @staticmethod
    def _generate_title_from_url(url: str) -> str:
        """
        Generate a title from the URL path.

        Args:
            url: PDF URL

        Returns:
            Human-readable title
        """
        # Extract filename from URL
        parsed = urlparse(url)
        filename = Path(parsed.path).stem

        # Clean up filename
        title = filename.replace("_", " ").replace("-", " ").title()

        return title or "Untitled Document"


class ManufacturerDocsScraper:
    """
    Unified interface for scraping manufacturer documentation.

    Handles common manufacturer documentation sources:
    - Rockwell Automation (Allen-Bradley)
    - Siemens
    - Mitsubishi
    - ABB
    - Schneider Electric
    """

    # Common manufacturer documentation URL patterns
    MANUFACTURER_DOMAINS = {
        "rockwellautomation.com": "Rockwell Automation",
        "siemens.com": "Siemens",
        "mitsubishielectric.com": "Mitsubishi Electric",
        "abb.com": "ABB",
        "se.com": "Schneider Electric",
    }

    def __init__(self):
        self.pdf_scraper = PDFScraper()

    def scrape(self, url: str) -> Optional[PDFResult]:
        """
        Scrape manufacturer documentation.

        Args:
            url: URL to documentation (PDF)

        Returns:
            PDFResult or None
        """
        # Detect manufacturer
        manufacturer = self._detect_manufacturer(url)

        result = self.pdf_scraper.scrape(url)

        # Add manufacturer to metadata
        if result and manufacturer:
            result.metadata["manufacturer"] = manufacturer

        return result

    def scrape_batch(self, urls: List[str]) -> List[PDFResult]:
        """Scrape multiple manufacturer documents."""
        return self.pdf_scraper.scrape_batch(urls)

    def _detect_manufacturer(self, url: str) -> Optional[str]:
        """
        Detect manufacturer from URL.

        Args:
            url: Documentation URL

        Returns:
            Manufacturer name or None
        """
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        for pattern, manufacturer in self.MANUFACTURER_DOMAINS.items():
            if pattern in domain:
                return manufacturer

        return None


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Example manufacturer documentation URLs
    test_urls = [
        "https://literature.rockwellautomation.com/idc/groups/literature/documents/um/1756-um001_-en-p.pdf",
        "https://cache.industry.siemens.com/dl/files/465/36932465/att_106119/v1/s71200_system_manual_en-US_en-US.pdf"
    ]

    scraper = ManufacturerDocsScraper()

    for url in test_urls:
        result = scraper.scrape(url)
        if result:
            print(f"\nTitle: {result.title}")
            print(f"Manufacturer: {result.metadata.get('manufacturer', 'Unknown')}")
            print(f"Pages: {result.metadata.get('pages', 0)}")
            print(f"Content preview: {result.content[:200]}...")

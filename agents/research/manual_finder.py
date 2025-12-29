"""
ManualFinder Agent - Find and deliver equipment manuals in <5 seconds.

Searches manufacturer catalogs and web sources for PDF manuals,
with intelligent query reformulation using LLM and local caching.
"""

import asyncio
import hashlib
import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import logging

import httpx
from groq import Groq

# Import Phoenix tracer if available
try:
    from phoenix_integration.phoenix_tracer import traced
except ImportError:
    # Fallback no-op decorator
    def traced(agent_name=None):
        def decorator(func):
            return func
        return decorator

logger = logging.getLogger(__name__)


@dataclass
class ManualResult:
    """Result from manual search."""
    pdf_url: str
    pdf_local_path: Optional[str] = None
    page_count: int = 0
    file_size_mb: float = 0.0
    source: str = "unknown"  # 'manufacturer', 'web', 'cache'
    confidence: float = 0.0
    title: str = ""

    def to_dict(self) -> dict:
        """Convert to dict for serialization."""
        return asdict(self)


class ManualFinder:
    """
    Find equipment manuals from manufacturer catalogs and web sources.

    Strategy:
    1. Check local cache first (24h TTL)
    2. Search manufacturer-specific catalog (Siemens, Rockwell, ABB)
    3. Fallback to web search with LLM query reformulation
    4. Download and cache PDF if found
    """

    def __init__(self, cache_dir: str = "/tmp/manuals"):
        """
        Initialize ManualFinder.

        Args:
            cache_dir: Directory for PDF cache
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize Groq for query reformulation
        groq_api_key = os.getenv("GROQ_API_KEY")
        self.groq_client = Groq(api_key=groq_api_key) if groq_api_key else None

        # HTTP client for downloads
        self.http_client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)

    @traced(agent_name="manual_finder")
    async def find_manual(
        self,
        model: str,
        manufacturer: str
    ) -> Optional[ManualResult]:
        """
        Main entry point - find manual for equipment model.

        Args:
            model: Equipment model (e.g., "G120", "S7-1200")
            manufacturer: Manufacturer name (e.g., "Siemens", "Rockwell")

        Returns:
            ManualResult if found, None otherwise
        """
        logger.info(f"Finding manual for {manufacturer} {model}")

        try:
            # Step 1: Check cache
            cached = await self._check_cache(model, manufacturer)
            if cached:
                logger.info(f"✅ Manual found in cache")
                return cached

            # Step 2: Search manufacturer catalog
            catalog_results = await self.search_manufacturer_catalog(manufacturer, model)
            if catalog_results:
                manual = catalog_results[0]
                logger.info(f"✅ Manual found in manufacturer catalog")

                # Download and cache
                local_path = await self.download_and_cache_pdf(
                    manual['url'],
                    model,
                    manufacturer
                )

                return ManualResult(
                    pdf_url=manual['url'],
                    pdf_local_path=local_path,
                    page_count=manual.get('pages', 0),
                    file_size_mb=manual.get('size_mb', 0.0),
                    source="manufacturer",
                    confidence=0.9,
                    title=manual.get('title', f"{manufacturer} {model} Manual")
                )

            # Step 3: Fallback to web search
            web_results = await self.search_web_for_manual(model, manufacturer)
            if web_results:
                manual = web_results[0]
                logger.info(f"✅ Manual found via web search")

                # Download and cache
                local_path = await self.download_and_cache_pdf(
                    manual['url'],
                    model,
                    manufacturer
                )

                return ManualResult(
                    pdf_url=manual['url'],
                    pdf_local_path=local_path,
                    page_count=0,  # Unknown from web search
                    file_size_mb=0.0,
                    source="web",
                    confidence=0.7,
                    title=manual.get('title', f"{manufacturer} {model} Manual")
                )

            logger.warning(f"⚠️  No manual found for {manufacturer} {model}")
            return None

        except Exception as e:
            logger.error(f"❌ Error finding manual: {e}", exc_info=True)
            return None

    async def search_manufacturer_catalog(
        self,
        manufacturer: str,
        model: str
    ) -> list[dict]:
        """
        Search manufacturer-specific catalogs.

        Args:
            manufacturer: Manufacturer name
            model: Equipment model

        Returns:
            List of manual dicts with url, title, pages, size_mb
        """
        manufacturer_lower = manufacturer.lower()

        # Manufacturer-specific search URLs
        search_patterns = {
            "siemens": f"support.industry.siemens.com/cs/document {model}",
            "rockwell": f"literature.rockwellautomation.com {model}",
            "allen-bradley": f"literature.rockwellautomation.com {model}",
            "abb": f"library.abb.com {model}",
            "schneider": f"product-catalog.schneider-electric.com {model}",
            "mitsubishi": f"www.mitsubishielectric.com {model} manual",
            "fanuc": f"www.fanuc.com {model} manual pdf",
        }

        search_url = search_patterns.get(manufacturer_lower)
        if not search_url:
            logger.debug(f"No catalog search pattern for {manufacturer}")
            return []

        # NOTE: This is a simplified implementation
        # In production, you'd use manufacturer-specific APIs or scraping
        logger.debug(f"Would search: {search_url}")

        # Placeholder - return empty for now
        # Real implementation would:
        # 1. HTTP GET to manufacturer catalog
        # 2. Parse HTML/JSON response
        # 3. Extract PDF links and metadata
        return []

    async def search_web_for_manual(
        self,
        model: str,
        manufacturer: str
    ) -> list[dict]:
        """
        Search web for manual using LLM query reformulation.

        Args:
            model: Equipment model
            manufacturer: Manufacturer name

        Returns:
            List of manual dicts with url, title
        """
        # Step 1: Reformulate query using Groq
        if self.groq_client:
            reformulated_query = await self._reformulate_query(model, manufacturer)
        else:
            reformulated_query = f'"{manufacturer} {model} manual PDF filetype:pdf"'

        logger.debug(f"Web search query: {reformulated_query}")

        # Step 2: Web search (simplified placeholder)
        # Real implementation would use:
        # - Google Custom Search API
        # - DuckDuckGo API
        # - SerpAPI
        # - Manual download sites (manualslib.com, etc.)

        # Placeholder - return empty for now
        return []

    async def download_and_cache_pdf(
        self,
        url: str,
        model: str,
        manufacturer: str
    ) -> str:
        """
        Download PDF and cache locally.

        Args:
            url: PDF URL
            model: Equipment model
            manufacturer: Manufacturer name

        Returns:
            Local file path
        """
        # Generate cache filename from URL hash
        url_hash = hashlib.sha256(url.encode()).hexdigest()
        pdf_path = self.cache_dir / f"{url_hash}.pdf"
        meta_path = self.cache_dir / f"{url_hash}.meta.json"

        try:
            # Download PDF
            logger.info(f"Downloading PDF from {url}")
            response = await self.http_client.get(url)
            response.raise_for_status()

            # Write to cache
            pdf_path.write_bytes(response.content)

            # Write metadata
            metadata = {
                "url": url,
                "model": model,
                "manufacturer": manufacturer,
                "downloaded_at": datetime.now().isoformat(),
                "file_size_bytes": len(response.content),
                "file_size_mb": len(response.content) / (1024 * 1024)
            }
            meta_path.write_text(json.dumps(metadata, indent=2))

            logger.info(f"✅ PDF cached to {pdf_path}")
            return str(pdf_path)

        except Exception as e:
            logger.error(f"❌ Error downloading PDF: {e}", exc_info=True)
            return ""

    async def _check_cache(
        self,
        model: str,
        manufacturer: str
    ) -> Optional[ManualResult]:
        """
        Check local cache for manual.

        Args:
            model: Equipment model
            manufacturer: Manufacturer name

        Returns:
            ManualResult if cached and fresh (<24h), None otherwise
        """
        # Scan cache directory for matching metadata
        for meta_path in self.cache_dir.glob("*.meta.json"):
            try:
                metadata = json.loads(meta_path.read_text())

                # Check if matches
                if (metadata.get("model") == model and
                    metadata.get("manufacturer") == manufacturer):

                    # Check TTL (24 hours)
                    downloaded_at = datetime.fromisoformat(metadata["downloaded_at"])
                    age = datetime.now() - downloaded_at
                    if age < timedelta(hours=24):
                        # Cache hit!
                        pdf_path = meta_path.with_suffix(".pdf")
                        if pdf_path.exists():
                            return ManualResult(
                                pdf_url=metadata["url"],
                                pdf_local_path=str(pdf_path),
                                page_count=0,  # Would need PDF parsing to get this
                                file_size_mb=metadata.get("file_size_mb", 0.0),
                                source="cache",
                                confidence=1.0,
                                title=f"{manufacturer} {model} Manual"
                            )

            except Exception as e:
                logger.debug(f"Error reading cache metadata: {e}")
                continue

        return None

    async def _reformulate_query(
        self,
        model: str,
        manufacturer: str
    ) -> str:
        """
        Use Groq to reformulate search query.

        Examples:
        - Input: "G120" → Output: "Siemens SINAMICS G120 inverter manual PDF"
        - Input: "1756-L8" → Output: "Allen-Bradley ControlLogix 1756-L8 user manual"

        Args:
            model: Equipment model
            manufacturer: Manufacturer name

        Returns:
            Reformulated search query
        """
        if not self.groq_client:
            return f'"{manufacturer} {model} manual PDF filetype:pdf"'

        try:
            prompt = f"""You are an industrial equipment expert. Reformulate this search query to find the official PDF manual:

Model: {model}
Manufacturer: {manufacturer}

Return ONLY the search query (no explanation). Include:
1. Full product name if you recognize abbreviations
2. "manual" or "user guide" keyword
3. "PDF" keyword

Examples:
- G120 → "Siemens SINAMICS G120 inverter manual PDF"
- 1756-L8 → "Allen-Bradley ControlLogix 1756-L8 user manual PDF"
- S7-1200 → "Siemens S7-1200 PLC programming manual PDF"
"""

            response = self.groq_client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=100
            )

            reformulated = response.choices[0].message.content.strip().strip('"')
            logger.info(f"Reformulated query: {reformulated}")
            return reformulated

        except Exception as e:
            logger.error(f"Error reformulating query: {e}", exc_info=True)
            return f'"{manufacturer} {model} manual PDF filetype:pdf"'

    async def close(self):
        """Close HTTP client."""
        await self.http_client.aclose()

    def __del__(self):
        """Cleanup on deletion."""
        try:
            import asyncio
            if hasattr(self, 'http_client'):
                asyncio.create_task(self.http_client.aclose())
        except:
            pass

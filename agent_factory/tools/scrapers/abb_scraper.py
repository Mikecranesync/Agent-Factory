"""
ABB Library scraper for industrial equipment manuals.

ABB has a structured library at library.abb.com with:
- Motor drives (VFDs)
- Switchgear
- Robotics
- Power equipment

STRATEGY:
- Use Google Custom Search API with site:library.abb.com
- Extract PDFs from search results
- Parse metadata from filenames and page content
"""

import re
import time
from typing import List, Optional
from datetime import datetime
from urllib.parse import urljoin, urlparse

from agent_factory.models.manual import (
    EquipmentManual,
    ManualMetadata,
    ManualType
)
from .base_scraper import BaseScraper, ScrapeResult, ScrapeStatus


class ABBScraper(BaseScraper):
    """
    Scraper for ABB equipment manuals.

    Uses Google Custom Search API to find manuals on library.abb.com.
    """

    BASE_URL = "https://library.abb.com"
    MANUFACTURER = "ABB"

    # Equipment type search queries
    EQUIPMENT_QUERIES = {
        "motor_drives": [
            "ACS880 service manual",
            "ACS580 service manual",
            "ACH580 service manual",
            "ACS355 service manual"
        ],
        "vfd": [
            "VFD service manual",
            "variable frequency drive manual",
            "drive troubleshooting"
        ],
        "switchgear": [
            "switchgear manual",
            "circuit breaker manual",
            "ZX series manual"
        ]
    }

    def __init__(
        self,
        google_api_key: Optional[str] = None,
        google_cse_id: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize ABB scraper.

        Args:
            google_api_key: Google Custom Search API key
            google_cse_id: Google Custom Search Engine ID
        """
        super().__init__(**kwargs)
        self.google_api_key = google_api_key
        self.google_cse_id = google_cse_id

        # Rate limiting
        self.last_request_time = 0

    def scrape(
        self,
        equipment_types: Optional[List[str]] = None,
        limit: Optional[int] = None
    ) -> ScrapeResult:
        """
        Scrape ABB library for manuals.

        Args:
            equipment_types: Equipment types to search (e.g., ["motor_drives", "vfd"])
            limit: Maximum manuals to scrape (for testing)

        Returns:
            ScrapeResult with found manuals
        """
        self.started_at = datetime.utcnow()
        manuals: List[EquipmentManual] = []
        errors: List[str] = []

        # Default to motor drives if not specified
        if not equipment_types:
            equipment_types = ["motor_drives"]

        self._log(f"Starting ABB scrape for equipment types: {equipment_types}")

        # Search for each equipment type
        for eq_type in equipment_types:
            if eq_type not in self.EQUIPMENT_QUERIES:
                errors.append(f"Unknown equipment type: {eq_type}")
                continue

            try:
                type_manuals = self._scrape_equipment_type(eq_type, limit)
                manuals.extend(type_manuals)

                if limit and len(manuals) >= limit:
                    self._log(f"Reached limit of {limit} manuals")
                    break

            except Exception as e:
                error_msg = f"Error scraping {eq_type}: {str(e)}"
                errors.append(error_msg)
                self._log(error_msg, "ERROR")

        self.completed_at = datetime.utcnow()

        # Determine status
        if manuals and not errors:
            status = ScrapeStatus.SUCCESS
        elif manuals and errors:
            status = ScrapeStatus.PARTIAL
        elif not manuals and errors:
            status = ScrapeStatus.FAILED
        else:
            status = ScrapeStatus.FAILED

        self._log(f"Scrape complete: {len(manuals)} manuals, {len(errors)} errors")

        return ScrapeResult(
            status=status,
            manuals=manuals,
            errors=errors,
            metadata=self.get_statistics()
        )

    def _scrape_equipment_type(
        self,
        equipment_type: str,
        limit: Optional[int] = None
    ) -> List[EquipmentManual]:
        """
        Scrape manuals for a specific equipment type.

        Args:
            equipment_type: Equipment type key
            limit: Maximum manuals to return

        Returns:
            List of EquipmentManual objects
        """
        queries = self.EQUIPMENT_QUERIES.get(equipment_type, [])
        manuals: List[EquipmentManual] = []

        for query in queries:
            # Rate limiting
            self._apply_rate_limit()

            try:
                results = self._google_search(query, limit=10)
                self.requests_made += 1

                for result in results:
                    if limit and len(manuals) >= limit:
                        break

                    manual = self._parse_search_result(result, equipment_type)
                    if manual:
                        manuals.append(manual)

            except Exception as e:
                self._log(f"Search error for '{query}': {str(e)}", "ERROR")

            if limit and len(manuals) >= limit:
                break

        return manuals

    def _google_search(self, query: str, limit: int = 10) -> List[dict]:
        """
        Search using Google Custom Search API.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of search result dictionaries
        """
        if not self.google_api_key or not self.google_cse_id:
            self._log("Google API credentials not provided - returning mock results", "WARNING")
            return self._mock_search_results(query)

        # TODO: Implement real Google Custom Search
        # from googleapiclient.discovery import build
        # service = build("customsearch", "v1", developerKey=self.google_api_key)
        # site_query = f'site:{self.BASE_URL} {query} filetype:pdf'
        # result = service.cse().list(q=site_query, cx=self.google_cse_id, num=limit).execute()
        # return result.get('items', [])

        # For now, return mock results
        return self._mock_search_results(query)

    def _mock_search_results(self, query: str) -> List[dict]:
        """
        Generate mock search results for testing.

        Returns realistic ABB manual structure.
        """
        # Extract model from query (e.g., "ACS880" from "ACS880 service manual")
        model_match = re.search(r'(ACS\d+|ACH\d+|VFD|ZX)', query)
        model = model_match.group(1) if model_match else "UNKNOWN"

        return [
            {
                "title": f"{model} Drive Service Manual - ABB Library",
                "link": f"{self.BASE_URL}/manuals/{model.lower()}-service-manual.pdf",
                "snippet": f"Complete service and troubleshooting manual for ABB {model} variable frequency drive. Includes diagnostic procedures, error codes, and maintenance schedules.",
                "fileFormat": "PDF",
                "pagemap": {
                    "metatags": [{
                        "title": f"{model} Service Manual v2.1",
                        "author": "ABB",
                        "subject": "Service Manual"
                    }]
                }
            },
            {
                "title": f"{model} Installation Guide - ABB Library",
                "link": f"{self.BASE_URL}/manuals/{model.lower()}-installation.pdf",
                "snippet": f"Installation and commissioning guide for {model} drives. Wiring diagrams and startup procedures.",
                "fileFormat": "PDF"
            }
        ]

    def _parse_search_result(self, result: dict, equipment_type: str) -> Optional[EquipmentManual]:
        """
        Parse Google search result into EquipmentManual.

        Args:
            result: Google search result dictionary
            equipment_type: Equipment type category

        Returns:
            EquipmentManual if valid, None if should be skipped
        """
        title = result.get("title", "")
        url = result.get("link", "")
        snippet = result.get("snippet", "")

        # Skip if not a PDF
        if not url.endswith(".pdf"):
            return None

        # Skip if low quality indicators
        if self._should_skip_manual(title, url):
            return None

        # Extract model number from title or URL
        model = self._extract_model_number(title, url)

        # Determine manual type
        manual_type = self._categorize_manual_type(title, url)

        # Generate unique manual ID
        manual_id = f"ABB-{model}-{manual_type.value}".upper()

        # Create metadata
        metadata = ManualMetadata(
            manufacturer=self.MANUFACTURER,
            equipment_model=model,
            equipment_name=f"ABB {model}",
            manual_type=manual_type,
            manual_title=title,
            source_url=url,
            discovered_at=datetime.utcnow(),
            last_updated=datetime.utcnow()
        )

        # Create manual
        manual = EquipmentManual(
            manual_id=manual_id,
            metadata=metadata,
            raw_content=snippet,  # Search snippet as preview
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        # Calculate quality score
        quality_score = self._extract_quality_score(manual)
        manual.metadata.quality_score = quality_score

        self._log(f"Found: {manual_id} (quality: {quality_score:.2f})")

        return manual

    def _extract_model_number(self, title: str, url: str) -> str:
        """
        Extract ABB model number from title or URL.

        ABB models: ACS880, ACS580, ACH580, ACS355, etc.
        """
        text = f"{title} {url}"

        # Try common ABB model patterns
        patterns = [
            r'(ACS\d+)',  # ACS880, ACS580, etc.
            r'(ACH\d+)',  # ACH580, etc.
            r'(ACS[A-Z]\d+)',  # ACST880, etc.
            r'(VFD-\d+)',  # VFD models
            r'(ZX\d+)',   # Switchgear
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).upper()

        # Fallback: generic model
        return "UNKNOWN-MODEL"

    def _apply_rate_limit(self):
        """Apply rate limiting between requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - elapsed
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def search_manuals(self, query: str, limit: int = 10) -> ScrapeResult:
        """
        Search ABB library for specific manuals.

        Args:
            query: Search query (model number, equipment name, etc.)
            limit: Maximum results

        Returns:
            ScrapeResult with matching manuals
        """
        self.started_at = datetime.utcnow()
        manuals: List[EquipmentManual] = []
        errors: List[str] = []

        try:
            # Apply rate limiting
            self._apply_rate_limit()

            # Search
            results = self._google_search(query, limit=limit)
            self.requests_made += 1

            # Parse results
            for result in results:
                manual = self._parse_search_result(result, "search_result")
                if manual:
                    manuals.append(manual)

        except Exception as e:
            errors.append(f"Search error: {str(e)}")

        self.completed_at = datetime.utcnow()

        status = ScrapeStatus.SUCCESS if manuals else ScrapeStatus.FAILED

        return ScrapeResult(
            status=status,
            manuals=manuals,
            errors=errors,
            metadata=self.get_statistics()
        )

    def get_manual_by_id(self, manual_id: str) -> Optional[EquipmentManual]:
        """
        Fetch specific ABB manual by ID.

        Args:
            manual_id: Manual identifier (e.g., "ABB-ACS880-SERVICE")

        Returns:
            EquipmentManual if found, None otherwise
        """
        # Parse manual ID to extract model and type
        parts = manual_id.split("-")
        if len(parts) < 3:
            return None

        model = parts[1]
        manual_type = parts[2].lower()

        # Search for this specific manual
        query = f"{model} {manual_type} manual"
        result = self.search_manuals(query, limit=1)

        if result.manuals:
            return result.manuals[0]

        return None

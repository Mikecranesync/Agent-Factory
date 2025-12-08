"""
Base scraper abstract class for manufacturer sites.

All manufacturer scrapers inherit from this to ensure consistent interface.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from agent_factory.models.manual import EquipmentManual, ManualMetadata, ManualType


class ScrapeStatus(str, Enum):
    """Status of a scrape operation."""
    SUCCESS = "success"
    PARTIAL = "partial"  # Some manuals found, some errors
    FAILED = "failed"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"


@dataclass
class ScrapeResult:
    """
    Result from a scraping operation.

    Includes both successful finds and errors for debugging.
    """
    status: ScrapeStatus
    manuals: List[EquipmentManual]
    errors: List[str]
    metadata: Dict[str, Any]  # Scraper-specific metadata

    @property
    def success_count(self) -> int:
        """Number of successfully scraped manuals."""
        return len(self.manuals)

    @property
    def error_count(self) -> int:
        """Number of errors encountered."""
        return len(self.errors)

    @property
    def is_successful(self) -> bool:
        """True if scrape was successful (found manuals, no critical errors)."""
        return self.status in (ScrapeStatus.SUCCESS, ScrapeStatus.PARTIAL)


class BaseScraper(ABC):
    """
    Abstract base class for manufacturer scrapers.

    Each manufacturer site has unique structure, so scrapers are customized.
    This base class enforces consistent interface.
    """

    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        rate_limit_delay: float = 1.0,
        user_agent: Optional[str] = None,
        verbose: bool = False
    ):
        """
        Initialize scraper.

        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts for failed requests
            rate_limit_delay: Delay between requests (seconds)
            user_agent: Custom user agent string
            verbose: Enable verbose logging
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.rate_limit_delay = rate_limit_delay
        self.user_agent = user_agent or self._default_user_agent()
        self.verbose = verbose

        # Statistics
        self.requests_made = 0
        self.bytes_downloaded = 0
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None

    @abstractmethod
    def scrape(
        self,
        equipment_types: Optional[List[str]] = None,
        limit: Optional[int] = None
    ) -> ScrapeResult:
        """
        Main scraping method - implemented by subclasses.

        Args:
            equipment_types: Filter to specific equipment types (e.g., ["VFD", "motor"])
            limit: Maximum number of manuals to scrape (for testing)

        Returns:
            ScrapeResult with found manuals and any errors
        """
        pass

    @abstractmethod
    def search_manuals(self, query: str, limit: int = 10) -> ScrapeResult:
        """
        Search manufacturer site for specific manuals.

        Args:
            query: Search query (model number, equipment name, etc.)
            limit: Maximum results to return

        Returns:
            ScrapeResult with matching manuals
        """
        pass

    @abstractmethod
    def get_manual_by_id(self, manual_id: str) -> Optional[EquipmentManual]:
        """
        Fetch a specific manual by manufacturer's ID.

        Args:
            manual_id: Manufacturer-specific manual identifier

        Returns:
            EquipmentManual if found, None otherwise
        """
        pass

    def _default_user_agent(self) -> str:
        """Default user agent for requests."""
        return (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )

    def _log(self, message: str, level: str = "INFO"):
        """Log message if verbose mode enabled."""
        if self.verbose:
            timestamp = datetime.utcnow().strftime("%H:%M:%S")
            print(f"[{timestamp}] [{level}] {message}")

    def _extract_quality_score(self, manual: EquipmentManual) -> float:
        """
        Calculate quality score for a manual.

        Factors:
        - Has publication date (+0.2)
        - Has version number (+0.1)
        - Page count > 10 (+0.2)
        - Has specifications (+0.2)
        - Has error codes (+0.2)
        - Has diagnostic flows (+0.1)

        Returns:
            Quality score from 0.0 to 1.0
        """
        score = 0.0

        if manual.metadata.publication_date:
            score += 0.2

        if manual.metadata.manual_version:
            score += 0.1

        if manual.metadata.page_count and manual.metadata.page_count > 10:
            score += 0.2

        if manual.specifications:
            score += 0.2

        if manual.error_codes:
            score += 0.2

        if manual.diagnostic_flows:
            score += 0.1

        return min(score, 1.0)

    def _categorize_manual_type(self, title: str, filename: str = "") -> ManualType:
        """
        Infer manual type from title and filename.

        Args:
            title: Manual title
            filename: Manual filename (optional)

        Returns:
            ManualType enum value
        """
        text = f"{title} {filename}".lower()

        if any(word in text for word in ["install", "installation", "setup"]):
            return ManualType.INSTALLATION
        elif any(word in text for word in ["service", "repair", "maintenance"]):
            return ManualType.SERVICE
        elif any(word in text for word in ["troubleshoot", "diagnostic", "fault", "error"]):
            return ManualType.TROUBLESHOOTING
        elif any(word in text for word in ["wiring", "electrical", "schematic"]):
            return ManualType.WIRING
        elif any(word in text for word in ["parts", "spare", "catalog"]):
            return ManualType.PARTS
        elif any(word in text for word in ["operator", "user", "operation"]):
            return ManualType.OPERATORS
        elif any(word in text for word in ["safety", "warning", "caution"]):
            return ManualType.SAFETY
        else:
            return ManualType.SERVICE  # Default

    def _should_skip_manual(self, title: str, filename: str = "") -> bool:
        """
        Determine if manual should be skipped (low quality indicators).

        Args:
            title: Manual title
            filename: Manual filename (optional)

        Returns:
            True if manual should be skipped
        """
        text = f"{title} {filename}".lower()

        # Skip marketing materials
        if any(word in text for word in ["brochure", "catalog", "flyer", "datasheet"]):
            return True

        # Skip quick reference cards (too short)
        if any(word in text for word in ["quick reference", "qr card", "pocket guide"]):
            return True

        # Skip old manuals (before 2000)
        if "19" in text and any(year in text for year in ["1990", "1991", "1992", "1993", "1994", "1995", "1996", "1997", "1998", "1999"]):
            return True

        return False

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get scraper statistics.

        Returns:
            Dictionary with scraping statistics
        """
        duration = None
        if self.started_at and self.completed_at:
            duration = (self.completed_at - self.started_at).total_seconds()

        return {
            "requests_made": self.requests_made,
            "bytes_downloaded": self.bytes_downloaded,
            "duration_seconds": duration,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


class GoogleCustomSearchScraper(BaseScraper):
    """
    Scraper using Google Custom Search API.

    Useful for manufacturers without structured libraries.
    Uses site: operator to search specific domains.
    """

    def __init__(
        self,
        api_key: str,
        search_engine_id: str,
        site_domain: str,
        **kwargs
    ):
        """
        Initialize Google Custom Search scraper.

        Args:
            api_key: Google API key
            search_engine_id: Custom Search Engine ID
            site_domain: Domain to search (e.g., "support.industry.siemens.com")
        """
        super().__init__(**kwargs)
        self.api_key = api_key
        self.search_engine_id = search_engine_id
        self.site_domain = site_domain

    def scrape(
        self,
        equipment_types: Optional[List[str]] = None,
        limit: Optional[int] = None
    ) -> ScrapeResult:
        """
        Scrape using Google Custom Search.

        Constructs queries like: site:domain.com "manual" "model XYZ"
        """
        # TODO: Implement Google Custom Search scraping
        # from googleapiclient.discovery import build
        # service = build("customsearch", "v1", developerKey=self.api_key)
        # results = service.cse().list(q=query, cx=self.search_engine_id).execute()
        raise NotImplementedError("Google Custom Search scraper not yet implemented")

    def search_manuals(self, query: str, limit: int = 10) -> ScrapeResult:
        """Search using Google Custom Search."""
        raise NotImplementedError("Google Custom Search scraper not yet implemented")

    def get_manual_by_id(self, manual_id: str) -> Optional[EquipmentManual]:
        """Get manual by ID (not applicable for Google Search)."""
        raise NotImplementedError("Not applicable for Google Search scraper")

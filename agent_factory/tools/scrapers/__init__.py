"""
Manufacturer-specific scrapers for equipment manuals.

Each manufacturer has unique site structure requiring custom scraping logic.
"""

from .base_scraper import BaseScraper, ScrapeResult, ScrapeStatus
from .abb_scraper import ABBScraper

__all__ = [
    "BaseScraper",
    "ScrapeResult",
    "ScrapeStatus",
    "ABBScraper"
]

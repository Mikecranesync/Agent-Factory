"""
RIVET Pro Research Pipeline (Phase 5).

Implements Route C (No KB Coverage) research functionality:
- Forum scrapers (Stack Overflow + Reddit)
- Manufacturer documentation scraper (PDFs)
- YouTube transcript fetcher
- Content validation pipeline
- Research pipeline orchestrator
- Multi-source knowledge acquisition
"""

from agent_factory.rivet_pro.research.forum_scraper import (
    ForumResult,
    StackOverflowScraper,
    RedditScraper,
    ForumScraper
)
from agent_factory.rivet_pro.research.pdf_scraper import (
    PDFResult,
    PDFScraper,
    ManufacturerDocsScraper
)
from agent_factory.rivet_pro.research.youtube_scraper import (
    YouTubeResult,
    YouTubeScraper,
    TechnicalYouTubeScraper
)
from agent_factory.rivet_pro.research.content_validator import (
    ValidationResult,
    ValidationLevel,
    ContentValidator
)
from agent_factory.rivet_pro.research.research_pipeline import (
    ResearchResult,
    ResearchPipeline
)

__all__ = [
    # Forum scrapers
    "ForumResult",
    "StackOverflowScraper",
    "RedditScraper",
    "ForumScraper",
    # PDF scrapers
    "PDFResult",
    "PDFScraper",
    "ManufacturerDocsScraper",
    # YouTube scrapers
    "YouTubeResult",
    "YouTubeScraper",
    "TechnicalYouTubeScraper",
    # Validation
    "ValidationResult",
    "ValidationLevel",
    "ContentValidator",
    # Pipeline
    "ResearchResult",
    "ResearchPipeline",
]

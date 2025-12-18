"""
Research Pipeline for RIVET Pro Phase 5.

Orchestrates multi-source research when Route C (No KB Coverage) is triggered.
Coordinates forum scraping, deduplication, and knowledge base ingestion.
"""

import hashlib
import logging
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

from agent_factory.rivet_pro.research.forum_scraper import ForumScraper, ForumResult
from agent_factory.rivet_pro.models import RivetIntent
from agent_factory.core.database_manager import DatabaseManager

logger = logging.getLogger(__name__)


@dataclass
class ResearchResult:
    """Result of research pipeline execution."""

    sources_found: List[str]  # URLs discovered
    sources_queued: int  # Number queued for ingestion
    estimated_completion: str  # Time estimate
    status: str  # "success", "partial", "failed"
    error_message: Optional[str] = None


class ResearchPipeline:
    """
    Orchestrates multi-source research for Route C (No KB Coverage).

    When the orchestrator detects no KB coverage for a query, this pipeline:
    1. Scrapes forums (Stack Overflow + Reddit)
    2. Checks for duplicate sources (source_fingerprints table)
    3. Queues unique sources for ingestion (via ingestion_chain)
    4. Returns immediate results with URLs + "ask again in 5 min" message
    """

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """
        Initialize research pipeline.

        Args:
            db_manager: Optional database manager (creates new if None)
        """
        self.forum_scraper = ForumScraper()
        self.db = db_manager or DatabaseManager()

    def run(self, intent: RivetIntent) -> ResearchResult:
        """
        Execute research pipeline for given intent.

        Args:
            intent: Parsed user intent (vendor, equipment, symptom)

        Returns:
            ResearchResult with URLs found and ingestion status
        """
        logger.info(f"Starting research pipeline for intent: {intent}")

        try:
            # Step 1: Build search query from intent
            query = self._build_query(intent)
            logger.info(f"Search query: {query}")

            # Step 2: Scrape forums
            forums = self._scrape_forums(query, intent)
            if not forums:
                return ResearchResult(
                    sources_found=[],
                    sources_queued=0,
                    estimated_completion="N/A",
                    status="failed",
                    error_message="No sources found from forums"
                )

            # Step 3: Check for duplicate sources
            unique_sources = self._check_fingerprints(forums)
            logger.info(f"Found {len(unique_sources)} unique sources (out of {len(forums)} total)")

            # Step 4: Queue for ingestion
            queued_count = self._queue_for_ingestion(unique_sources)

            # Step 5: Return immediate results
            return ResearchResult(
                sources_found=[f.url for f in forums],
                sources_queued=queued_count,
                estimated_completion="3-5 minutes",
                status="success" if queued_count > 0 else "partial"
            )

        except Exception as e:
            logger.error(f"Research pipeline failed: {e}", exc_info=True)
            return ResearchResult(
                sources_found=[],
                sources_queued=0,
                estimated_completion="N/A",
                status="failed",
                error_message=str(e)
            )

    def _build_query(self, intent: RivetIntent) -> str:
        """
        Build search query from intent fields.

        Args:
            intent: Parsed user intent

        Returns:
            Search query string
        """
        # Combine relevant fields into search query
        parts = []

        if intent.vendor:
            parts.append(intent.vendor)

        if intent.equipment_type:
            parts.append(intent.equipment_type)

        if intent.symptom:
            parts.append(intent.symptom)

        # Fallback to raw question if no structured fields
        if not parts and hasattr(intent, 'raw_question'):
            return intent.raw_question

        return " ".join(parts)

    def _scrape_forums(self, query: str, intent: RivetIntent) -> List[ForumResult]:
        """
        Scrape forums for relevant content.

        Args:
            query: Search query
            intent: User intent (for tag/subreddit selection)

        Returns:
            List of forum results
        """
        # Determine tags/subreddits based on intent
        stackoverflow_tags = self._get_stackoverflow_tags(intent)
        reddit_subreddits = self._get_reddit_subreddits(intent)

        # Execute forum search
        results = self.forum_scraper.search_all(
            query=query,
            stackoverflow_tags=stackoverflow_tags,
            reddit_subreddits=reddit_subreddits,
            limit=10
        )

        logger.info(f"Forum scraping found {len(results)} results")
        return results

    def _get_stackoverflow_tags(self, intent: RivetIntent) -> List[str]:
        """Get Stack Overflow tags based on intent."""
        tags = ["plc", "industrial-automation"]

        # Add vendor-specific tags
        if intent.vendor:
            vendor_lower = intent.vendor.lower()
            if "siemens" in vendor_lower:
                tags.append("siemens")
            elif "rockwell" in vendor_lower or "allen-bradley" in vendor_lower:
                tags.append("rockwell-automation")

        return tags

    def _get_reddit_subreddits(self, intent: RivetIntent) -> List[str]:
        """Get Reddit subreddits based on intent."""
        subreddits = ["PLC", "industrialmaintenance"]

        # Add topic-specific subreddits
        if intent.equipment_type:
            equipment_lower = intent.equipment_type.lower()
            if "motor" in equipment_lower or "drive" in equipment_lower:
                subreddits.append("electricians")
            if "automation" in equipment_lower:
                subreddits.append("automation")

        return subreddits

    def _check_fingerprints(self, sources: List[ForumResult]) -> List[ForumResult]:
        """
        Check which sources are already ingested (deduplication).

        Args:
            sources: List of forum results

        Returns:
            List of unique sources (not already in source_fingerprints table)
        """
        unique_sources = []

        for source in sources:
            fingerprint = self._compute_fingerprint(source.url)

            # Check if fingerprint exists in database
            if not self._fingerprint_exists(fingerprint):
                unique_sources.append(source)
            else:
                logger.debug(f"Skipping duplicate source: {source.url}")

        return unique_sources

    def _compute_fingerprint(self, url: str) -> str:
        """Compute SHA-256 fingerprint for URL."""
        return hashlib.sha256(url.encode('utf-8')).hexdigest()

    def _fingerprint_exists(self, fingerprint: str) -> bool:
        """
        Check if fingerprint exists in source_fingerprints table.

        Args:
            fingerprint: SHA-256 hash of URL

        Returns:
            True if fingerprint exists, False otherwise
        """
        try:
            conn = self.db.get_connection("supabase")
            if not conn:
                logger.warning("No database connection, assuming fingerprint doesn't exist")
                return False

            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT COUNT(*) FROM source_fingerprints WHERE url_hash = %s",
                    (fingerprint,)
                )
                count = cursor.fetchone()[0]
                return count > 0

        except Exception as e:
            logger.error(f"Error checking fingerprint: {e}")
            return False  # Assume doesn't exist on error

    def _queue_for_ingestion(self, sources: List[ForumResult]) -> int:
        """
        Queue sources for ingestion via ingestion_chain.

        Args:
            sources: List of unique forum results

        Returns:
            Number of sources successfully queued
        """
        queued_count = 0

        for source in sources:
            try:
                # Insert source fingerprint to mark as queued
                self._insert_fingerprint(source.url, source.source_type)

                # TODO: Call ingestion_chain.ingest_source(source.url) asynchronously
                # For now, just log the intent
                logger.info(f"Queued for ingestion: {source.url}")
                queued_count += 1

            except Exception as e:
                logger.error(f"Failed to queue source {source.url}: {e}")

        logger.info(f"Queued {queued_count}/{len(sources)} sources for ingestion")
        return queued_count

    def _insert_fingerprint(self, url: str, source_type: str) -> None:
        """
        Insert source fingerprint into database.

        Args:
            url: Source URL
            source_type: Type of source (stackoverflow, reddit, etc.)
        """
        try:
            conn = self.db.get_connection("supabase")
            if not conn:
                logger.warning("No database connection, skipping fingerprint insert")
                return

            fingerprint = self._compute_fingerprint(url)

            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO source_fingerprints (url_hash, url, source_type, created_at)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (url_hash) DO NOTHING
                    """,
                    (fingerprint, url, source_type, datetime.utcnow())
                )
                conn.commit()

        except Exception as e:
            logger.error(f"Error inserting fingerprint for {url}: {e}")


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Mock intent
    from agent_factory.rivet_pro.models import RivetIntent

    intent = RivetIntent(
        vendor="Mitsubishi",
        equipment_type="iQ-R PLC",
        symptom="ethernet connection"
    )

    pipeline = ResearchPipeline()
    result = pipeline.run(intent)

    print(f"\nResearch Pipeline Result:")
    print(f"  Status: {result.status}")
    print(f"  Sources found: {len(result.sources_found)}")
    print(f"  Sources queued: {result.sources_queued}")
    print(f"  Estimated completion: {result.estimated_completion}")

    if result.sources_found:
        print(f"\n  URLs:")
        for url in result.sources_found[:5]:
            print(f"    - {url}")

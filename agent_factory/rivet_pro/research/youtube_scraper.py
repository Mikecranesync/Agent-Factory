"""
YouTube transcript scraper for technical video content.

Retrieves video transcripts when Route C (No KB Coverage) is triggered.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
import requests

logger = logging.getLogger(__name__)


@dataclass
class YouTubeResult:
    """Result from YouTube video transcript extraction."""

    url: str
    title: str
    content: str  # Transcript text
    metadata: Dict[str, Any] = field(default_factory=dict)
    source_type: str = "youtube"


class YouTubeScraper:
    """
    Scrapes YouTube video transcripts.

    Features:
    - Extract transcripts from video URLs
    - Search YouTube for relevant videos
    - Handle auto-generated and manual transcripts
    - Support multiple languages (prefer English)
    """

    def __init__(self, max_retries: int = 3):
        """
        Initialize YouTube scraper.

        Args:
            max_retries: Maximum number of retries for API calls
        """
        self.max_retries = max_retries
        self.session = requests.Session()

    def scrape(self, video_url: str) -> Optional[YouTubeResult]:
        """
        Scrape transcript from a YouTube video.

        Args:
            video_url: YouTube video URL

        Returns:
            YouTubeResult or None if scraping failed
        """
        try:
            # Extract video ID
            video_id = self._extract_video_id(video_url)
            if not video_id:
                logger.error(f"Invalid YouTube URL: {video_url}")
                return None

            # Fetch transcript
            logger.info(f"Fetching transcript for video: {video_id}")
            transcript_data = self._fetch_transcript(video_id)
            if not transcript_data:
                logger.error(f"Failed to fetch transcript for {video_id}")
                return None

            # Format transcript text
            transcript_text = self._format_transcript(transcript_data)

            # Get video metadata
            metadata = self._get_video_metadata(video_id)

            result = YouTubeResult(
                url=f"https://www.youtube.com/watch?v={video_id}",
                title=metadata.get("title", f"YouTube Video {video_id}"),
                content=transcript_text,
                metadata=metadata
            )

            logger.info(f"Successfully scraped YouTube video: {result.title}")
            return result

        except Exception as e:
            logger.error(f"YouTube scraping failed for {video_url}: {e}", exc_info=True)
            return None

    def scrape_batch(self, video_urls: List[str]) -> List[YouTubeResult]:
        """
        Scrape transcripts from multiple YouTube videos.

        Args:
            video_urls: List of YouTube video URLs

        Returns:
            List of successfully scraped YouTubeResult objects
        """
        results = []

        for url in video_urls:
            result = self.scrape(url)
            if result:
                results.append(result)

        logger.info(f"Batch scraping completed: {len(results)}/{len(video_urls)} videos successful")
        return results

    def search(self, query: str, limit: int = 5) -> List[YouTubeResult]:
        """
        Search YouTube for videos matching query and extract transcripts.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of YouTubeResult objects
        """
        try:
            # Search for videos using YouTube Data API v3 (simplified for now)
            # TODO: Implement proper YouTube Data API integration
            logger.warning("YouTube search not fully implemented - using placeholder")
            return []

        except Exception as e:
            logger.error(f"YouTube search failed: {e}", exc_info=True)
            return []

    def _extract_video_id(self, url: str) -> Optional[str]:
        """
        Extract video ID from YouTube URL.

        Supports formats:
        - https://www.youtube.com/watch?v=VIDEO_ID
        - https://youtu.be/VIDEO_ID
        - https://www.youtube.com/embed/VIDEO_ID

        Args:
            url: YouTube URL

        Returns:
            Video ID or None
        """
        # Pattern 1: youtube.com/watch?v=ID
        if "youtube.com/watch" in url:
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)
            video_id = query_params.get("v", [None])[0]
            if video_id:
                return video_id

        # Pattern 2: youtu.be/ID
        if "youtu.be/" in url:
            parsed = urlparse(url)
            video_id = parsed.path.strip("/")
            if video_id:
                return video_id

        # Pattern 3: youtube.com/embed/ID
        if "youtube.com/embed/" in url:
            parsed = urlparse(url)
            match = re.search(r"/embed/([^/?]+)", parsed.path)
            if match:
                return match.group(1)

        return None

    def _fetch_transcript(self, video_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch transcript for video ID.

        Args:
            video_id: YouTube video ID

        Returns:
            List of transcript segments or None
        """
        try:
            # Try to get English transcript (prefer manual over auto-generated)
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

            # Try manual English transcript first
            try:
                transcript = transcript_list.find_manually_created_transcript(['en'])
                return transcript.fetch()
            except:
                pass

            # Fall back to auto-generated English transcript
            try:
                transcript = transcript_list.find_generated_transcript(['en'])
                return transcript.fetch()
            except:
                pass

            # Fall back to any available transcript
            try:
                transcript = transcript_list.find_transcript(['en'])
                return transcript.fetch()
            except:
                pass

            logger.warning(f"No English transcript found for {video_id}")
            return None

        except TranscriptsDisabled:
            logger.error(f"Transcripts are disabled for video {video_id}")
            return None
        except NoTranscriptFound:
            logger.error(f"No transcript found for video {video_id}")
            return None
        except Exception as e:
            logger.error(f"Failed to fetch transcript for {video_id}: {e}")
            return None

    def _format_transcript(self, transcript_data: List[Dict[str, Any]]) -> str:
        """
        Format transcript segments into readable text.

        Args:
            transcript_data: List of transcript segments

        Returns:
            Formatted transcript text
        """
        # Extract text from segments
        segments = [segment.get("text", "") for segment in transcript_data]

        # Join segments with spaces
        text = " ".join(segments)

        # Clean up formatting
        text = re.sub(r'\s+', ' ', text).strip()

        # Truncate if too long (prevent OOM)
        max_chars = 50000  # ~50KB of text
        if len(text) > max_chars:
            logger.warning(f"Transcript truncated from {len(text)} to {max_chars} chars")
            text = text[:max_chars]

        return text

    def _get_video_metadata(self, video_id: str) -> Dict[str, Any]:
        """
        Get video metadata (title, duration, etc.).

        Args:
            video_id: YouTube video ID

        Returns:
            Metadata dictionary
        """
        # TODO: Use YouTube Data API v3 for proper metadata
        # For now, return basic metadata

        metadata = {
            "video_id": video_id,
            "platform": "youtube",
        }

        return metadata


class TechnicalYouTubeScraper:
    """
    Specialized YouTube scraper for technical industrial content.

    Focuses on:
    - PLC programming tutorials
    - Troubleshooting guides
    - Equipment setup videos
    - Manufacturer training content
    """

    # Common technical YouTube channels
    TRUSTED_CHANNELS = [
        "RealPars",  # PLC training
        "PLCProfessor",
        "AutomationDirect",
        "RockwellAutomation",
        "SiemensIndustry",
    ]

    def __init__(self):
        self.youtube_scraper = YouTubeScraper()

    def scrape(self, video_url: str) -> Optional[YouTubeResult]:
        """
        Scrape technical YouTube video.

        Args:
            video_url: YouTube video URL

        Returns:
            YouTubeResult or None
        """
        result = self.youtube_scraper.scrape(video_url)

        # Add technical flags to metadata
        if result:
            result.metadata["technical_content"] = True

        return result

    def scrape_batch(self, video_urls: List[str]) -> List[YouTubeResult]:
        """Scrape multiple technical videos."""
        return self.youtube_scraper.scrape_batch(video_urls)

    def search(
        self,
        query: str,
        limit: int = 5,
        trusted_only: bool = False
    ) -> List[YouTubeResult]:
        """
        Search for technical videos.

        Args:
            query: Search query
            limit: Maximum results
            trusted_only: Only return videos from trusted channels

        Returns:
            List of YouTubeResult objects
        """
        # TODO: Implement YouTube search with channel filtering
        logger.warning("Technical YouTube search not fully implemented")
        return []


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Example technical YouTube videos
    test_urls = [
        "https://www.youtube.com/watch?v=RrqjoxZA0AM",  # PLC example
        "https://youtu.be/dQw4w9WgXcQ",  # Should fail (no transcript)
    ]

    scraper = TechnicalYouTubeScraper()

    for url in test_urls:
        result = scraper.scrape(url)
        if result:
            print(f"\nTitle: {result.title}")
            print(f"Video ID: {result.metadata.get('video_id', 'Unknown')}")
            print(f"Content preview: {result.content[:200]}...")
        else:
            print(f"\nFailed to scrape: {url}")

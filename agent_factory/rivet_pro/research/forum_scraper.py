"""
Forum scrapers for Stack Overflow and Reddit.

Retrieves technical discussions from forums when Route C (No KB Coverage) is triggered.
"""

import time
import requests
from dataclasses import dataclass, field
from typing import List, Dict, Any, Literal, Optional
from urllib.parse import quote_plus
import logging

logger = logging.getLogger(__name__)


@dataclass
class ForumResult:
    """Result from forum search."""

    source_type: Literal["stackoverflow", "reddit"]
    url: str
    title: str
    content: str  # Question + Answer concatenated
    metadata: Dict[str, Any] = field(default_factory=dict)


class StackOverflowScraper:
    """
    Scrapes Stack Overflow using the StackExchange API v2.3.

    API Limits: 300 requests/day (no authentication required)
    Rate Limiting: Exponential backoff on 429 responses
    """

    BASE_URL = "https://api.stackexchange.com/2.3"

    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self.session = requests.Session()

    def search(
        self,
        query: str,
        tags: Optional[List[str]] = None,
        limit: int = 5
    ) -> List[ForumResult]:
        """
        Search Stack Overflow for answered questions.

        Args:
            query: Search query string
            tags: List of tags to filter by (e.g., ["plc", "industrial-automation"])
            limit: Maximum number of results

        Returns:
            List of ForumResult objects
        """
        if tags is None:
            tags = ["plc", "industrial-automation"]

        params = {
            "site": "stackoverflow",
            "order": "desc",
            "sort": "votes",
            "q": query,
            "tagged": ";".join(tags),
            "filter": "withbody",  # Include answer bodies
            "pagesize": limit
        }

        try:
            response = self._make_request(f"{self.BASE_URL}/search/advanced", params)
            if not response:
                return []

            data = response.json()
            items = data.get("items", [])

            results = []
            for item in items:
                # Only include answered questions
                if not item.get("is_answered", False):
                    continue

                # Get accepted answer if available
                answer_id = item.get("accepted_answer_id")
                if answer_id:
                    answer_text = self._get_answer(answer_id)
                else:
                    answer_text = "[No accepted answer]"

                result = ForumResult(
                    source_type="stackoverflow",
                    url=item.get("link", ""),
                    title=item.get("title", ""),
                    content=f"QUESTION:\n{item.get('title', '')}\n\n{self._strip_html(item.get('body', ''))}\n\nANSWER:\n{answer_text}",
                    metadata={
                        "score": item.get("score", 0),
                        "view_count": item.get("view_count", 0),
                        "answer_count": item.get("answer_count", 0),
                        "tags": item.get("tags", [])
                    }
                )
                results.append(result)

            logger.info(f"Stack Overflow search found {len(results)} results for query: {query}")
            return results

        except Exception as e:
            logger.error(f"Stack Overflow search failed: {e}")
            return []

    def _get_answer(self, answer_id: int) -> str:
        """Fetch answer text by ID."""
        try:
            response = self._make_request(
                f"{self.BASE_URL}/answers/{answer_id}",
                {"site": "stackoverflow", "filter": "withbody"}
            )
            if response:
                data = response.json()
                items = data.get("items", [])
                if items:
                    return self._strip_html(items[0].get("body", ""))
        except Exception as e:
            logger.error(f"Failed to fetch answer {answer_id}: {e}")

        return "[Answer unavailable]"

    def _make_request(self, url: str, params: Dict[str, Any]) -> Optional[requests.Response]:
        """
        Make API request with exponential backoff retry.

        Returns:
            Response object or None if all retries failed
        """
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, params=params, timeout=10)

                # Rate limit handling
                if response.status_code == 429:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    logger.warning(f"Rate limited. Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    continue

                response.raise_for_status()
                return response

            except requests.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)

        return None

    @staticmethod
    def _strip_html(html: str) -> str:
        """Strip HTML tags from text (basic implementation)."""
        import re
        clean = re.sub(r'<[^>]+>', '', html)
        clean = re.sub(r'\s+', ' ', clean).strip()
        return clean[:1000]  # Limit to 1000 chars


class RedditScraper:
    """
    Scrapes Reddit using unauthenticated JSON endpoint.

    API Limits: 60 requests/minute (no authentication required)
    Rate Limiting: Respects X-Ratelimit-* headers
    """

    BASE_URL = "https://www.reddit.com"

    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "AgentFactory/1.0 (Industrial Automation Research Bot)"
        })

    def search(
        self,
        query: str,
        subreddits: Optional[List[str]] = None,
        limit: int = 5
    ) -> List[ForumResult]:
        """
        Search Reddit for relevant posts.

        Args:
            query: Search query string
            subreddits: List of subreddits to search (e.g., ["PLC", "industrialmaintenance"])
            limit: Maximum number of results

        Returns:
            List of ForumResult objects
        """
        if subreddits is None:
            subreddits = ["PLC", "industrialmaintenance", "electricians", "automation"]

        all_results = []

        for subreddit in subreddits:
            try:
                results = self._search_subreddit(subreddit, query, limit=2)  # 2 per subreddit
                all_results.extend(results)
            except Exception as e:
                logger.error(f"Reddit search failed for r/{subreddit}: {e}")
                continue

        # Sort by score and return top results
        all_results.sort(key=lambda x: x.metadata.get("score", 0), reverse=True)
        results = all_results[:limit]

        logger.info(f"Reddit search found {len(results)} results for query: {query}")
        return results

    def _search_subreddit(self, subreddit: str, query: str, limit: int) -> List[ForumResult]:
        """Search a specific subreddit."""
        url = f"{self.BASE_URL}/r/{subreddit}/search.json"
        params = {
            "q": query,
            "restrict_sr": "on",  # Restrict to subreddit
            "sort": "relevance",
            "limit": limit
        }

        response = self._make_request(url, params)
        if not response:
            return []

        data = response.json()
        posts = data.get("data", {}).get("children", [])

        results = []
        for post_data in posts:
            post = post_data.get("data", {})

            # Filter: score >= 5, num_comments >= 2
            if post.get("score", 0) < 5 or post.get("num_comments", 0) < 2:
                continue

            # Get top comment
            top_comment = self._get_top_comment(subreddit, post.get("id"))

            result = ForumResult(
                source_type="reddit",
                url=f"{self.BASE_URL}{post.get('permalink', '')}",
                title=post.get("title", ""),
                content=f"POST:\n{post.get('title', '')}\n\n{post.get('selftext', '')}\n\nTOP COMMENT:\n{top_comment}",
                metadata={
                    "score": post.get("score", 0),
                    "num_comments": post.get("num_comments", 0),
                    "subreddit": subreddit
                }
            )
            results.append(result)

        return results

    def _get_top_comment(self, subreddit: str, post_id: str) -> str:
        """Fetch top comment for a post."""
        try:
            url = f"{self.BASE_URL}/r/{subreddit}/comments/{post_id}.json"
            response = self._make_request(url, params={"limit": 1})
            if response:
                data = response.json()
                if len(data) > 1:
                    comments = data[1].get("data", {}).get("children", [])
                    if comments:
                        return comments[0].get("data", {}).get("body", "")[:500]
        except Exception as e:
            logger.error(f"Failed to fetch comment for post {post_id}: {e}")

        return "[No comments]"

    def _make_request(self, url: str, params: Dict[str, Any]) -> Optional[requests.Response]:
        """
        Make API request with retry logic.

        Returns:
            Response object or None if failed
        """
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, params=params, timeout=10)

                # Check rate limit headers
                remaining = response.headers.get("X-Ratelimit-Remaining")
                if remaining and int(remaining) < 5:
                    logger.warning(f"Reddit rate limit low: {remaining} requests remaining")

                response.raise_for_status()
                return response

            except requests.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)

        return None


class ForumScraper:
    """
    Unified forum scraper interface.

    Searches both Stack Overflow and Reddit in parallel.
    """

    def __init__(self):
        self.stackoverflow = StackOverflowScraper()
        self.reddit = RedditScraper()

    def search_all(
        self,
        query: str,
        stackoverflow_tags: Optional[List[str]] = None,
        reddit_subreddits: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[ForumResult]:
        """
        Search all forums for relevant content.

        Args:
            query: Search query string
            stackoverflow_tags: Tags for Stack Overflow search
            reddit_subreddits: Subreddits for Reddit search
            limit: Maximum total results

        Returns:
            List of ForumResult objects (combined from all sources)
        """
        results = []

        # Stack Overflow search
        try:
            so_results = self.stackoverflow.search(query, tags=stackoverflow_tags, limit=5)
            results.extend(so_results)
        except Exception as e:
            logger.error(f"Stack Overflow search failed: {e}")

        # Reddit search
        try:
            reddit_results = self.reddit.search(query, subreddits=reddit_subreddits, limit=5)
            results.extend(reddit_results)
        except Exception as e:
            logger.error(f"Reddit search failed: {e}")

        # Sort by relevance score (favor Stack Overflow, then Reddit score)
        def sort_key(r: ForumResult) -> int:
            if r.source_type == "stackoverflow":
                return r.metadata.get("score", 0) * 2  # Weight SO higher
            else:
                return r.metadata.get("score", 0)

        results.sort(key=sort_key, reverse=True)

        # Return top N results
        limited_results = results[:limit]

        logger.info(f"Forum search completed: {len(limited_results)} total results ({query})")
        return limited_results


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    scraper = ForumScraper()
    results = scraper.search_all("Mitsubishi iQ-R PLC ethernet connection")

    for i, result in enumerate(results, 1):
        print(f"\n{i}. [{result.source_type.upper()}] {result.title}")
        print(f"   URL: {result.url}")
        print(f"   Score: {result.metadata.get('score', 0)}")
        print(f"   Content preview: {result.content[:200]}...")

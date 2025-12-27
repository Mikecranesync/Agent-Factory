"""
Manual Search Service

Wrapper around VectorStore with formatted results and filtering.
Returns search results with snippets and metadata for API consumption.

Usage:
    service = ManualSearchService()
    results = service.search(
        query="PowerFlex 525 fault F001",
        manufacturer="Allen-Bradley",
        top_k=5
    )
"""

import logging
from typing import List, Dict, Optional

from agent_factory.knowledge.vector_store import VectorStore
from agent_factory.rivet_pro.database import RIVETProDatabase

logger = logging.getLogger(__name__)


class ManualSearchService:
    """
    High-level manual search service.

    Features:
    - Search with manufacturer/family filtering
    - Formatted results with snippets
    - Metadata enrichment
    - Result ranking
    """

    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        db: Optional[RIVETProDatabase] = None
    ):
        """
        Initialize search service.

        Args:
            vector_store: VectorStore instance (creates new if None)
            db: RIVETProDatabase instance (creates new if None)
        """
        self.vector_store = vector_store or VectorStore()
        self.db = db or RIVETProDatabase()

    def search(
        self,
        query: str,
        manufacturer: Optional[str] = None,
        component_family: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict]:
        """
        Search equipment manuals.

        Args:
            query: Search query text
            manufacturer: Filter by manufacturer (e.g., "Allen-Bradley")
            component_family: Filter by component family (e.g., "VFD")
            top_k: Number of results to return

        Returns:
            List of search results:
            [
                {
                    "manual_id": "uuid",
                    "title": "Allen-Bradley PowerFlex 525 User Manual",
                    "manufacturer": "Allen-Bradley",
                    "component_family": "VFD",
                    "snippet": "...relevant text snippet...",
                    "score": 0.95,
                    "distance": 0.05
                }
            ]
        """
        logger.info(f"Searching manuals: query='{query}', mfr={manufacturer}, family={component_family}")

        # Phase 1: Use database search (lexical)
        # Phase 2: Use vector store search (semantic)
        db_results = self.db.search_manuals(
            manufacturer=manufacturer,
            component_family=component_family
        )

        # Format results
        formatted_results = []
        for idx, manual in enumerate(db_results[:top_k]):
            # Create snippet from title (Phase 1)
            # Phase 2: Use actual chunk text with query highlighting
            snippet = self._create_snippet(manual['title'], query)

            formatted_results.append({
                "manual_id": str(manual['id']),
                "title": manual['title'],
                "manufacturer": manual['manufacturer'],
                "component_family": manual['component_family'],
                "snippet": snippet,
                "score": 1.0 / (idx + 1),  # Simple ranking
                "distance": idx / 100.0     # Placeholder distance
            })

        logger.info(f"Found {len(formatted_results)} results")
        return formatted_results

    def search_by_fault_code(
        self,
        fault_code: str,
        manufacturer: Optional[str] = None
    ) -> List[Dict]:
        """
        Search manuals for specific fault code.

        Args:
            fault_code: Fault code (e.g., "F001", "E04")
            manufacturer: Filter by manufacturer

        Returns:
            List of search results (same format as search())
        """
        # Construct fault-specific query
        query = f"fault code {fault_code} troubleshooting"
        return self.search(query, manufacturer=manufacturer)

    def get_manual_details(self, manual_id: str) -> Optional[Dict]:
        """
        Get full details for a specific manual.

        Args:
            manual_id: Manual UUID

        Returns:
            Manual details dict or None if not found
        """
        # Query database for manual details
        manuals = self.db.search_manuals()

        for manual in manuals:
            if str(manual['id']) == manual_id:
                return {
                    "manual_id": str(manual['id']),
                    "title": manual['title'],
                    "manufacturer": manual['manufacturer'],
                    "component_family": manual['component_family'],
                    "file_path": manual.get('file_path'),
                    "indexed_at": manual.get('indexed_at'),
                    "page_count": manual.get('page_count')
                }

        return None

    def list_all_manuals(
        self,
        manufacturer: Optional[str] = None,
        component_family: Optional[str] = None
    ) -> List[Dict]:
        """
        List all indexed manuals.

        Args:
            manufacturer: Filter by manufacturer
            component_family: Filter by component family

        Returns:
            List of manual summaries
        """
        manuals = self.db.search_manuals(
            manufacturer=manufacturer,
            component_family=component_family
        )

        return [
            {
                "manual_id": str(m['id']),
                "title": m['title'],
                "manufacturer": m['manufacturer'],
                "component_family": m['component_family'],
                "indexed_at": m.get('indexed_at')
            }
            for m in manuals
        ]

    def get_manual_gaps(self, limit: int = 10) -> List[Dict]:
        """
        Get top requested missing manuals.

        Args:
            limit: Max number of gaps to return

        Returns:
            List of gap records:
            [
                {
                    "manufacturer": "Siemens",
                    "component_family": "PLC",
                    "request_count": 5,
                    "model_pattern": "S7-1200"
                }
            ]
        """
        gaps = self.db.get_top_manual_gaps(limit=limit)

        return [
            {
                "manufacturer": g['manufacturer'],
                "component_family": g['component_family'],
                "request_count": g['request_count'],
                "model_pattern": g.get('model_pattern'),
                "first_requested_at": g.get('first_requested_at'),
                "last_requested_at": g.get('last_requested_at')
            }
            for g in gaps
        ]

    def _create_snippet(self, text: str, query: str, max_length: int = 200) -> str:
        """
        Create a snippet from text, highlighting query matches.

        Args:
            text: Full text
            query: Search query
            max_length: Max snippet length

        Returns:
            Snippet with "..." ellipsis if truncated
        """
        # Phase 1: Simple truncation
        # Phase 2: Extract actual relevant chunk with query highlighting

        if len(text) <= max_length:
            return text

        # Try to find query in text
        text_lower = text.lower()
        query_lower = query.lower()

        if query_lower in text_lower:
            # Extract snippet around query match
            match_pos = text_lower.find(query_lower)
            start = max(0, match_pos - 50)
            end = min(len(text), match_pos + 150)

            snippet = text[start:end]
            if start > 0:
                snippet = "..." + snippet
            if end < len(text):
                snippet = snippet + "..."

            return snippet

        # No match, just return start of text
        return text[:max_length] + "..."

    def close(self):
        """Close all connections"""
        if self.vector_store:
            self.vector_store.close()
        if self.db:
            self.db.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

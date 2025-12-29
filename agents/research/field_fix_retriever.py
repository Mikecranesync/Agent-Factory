"""
FieldFixRetriever Agent - Find historical fixes from CMMS and interaction logs.

Queries multiple data sources:
1. CMMS work orders (via Atlas CMMS integration if available)
2. User interaction history
3. Extraction corrections (technician gold data)

Ranks by recency, similarity, and success confirmation.
"""

import asyncio
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Optional
import logging
import math

from agent_factory.core.database_manager import DatabaseManager

# Import Phoenix tracer if available
try:
    from phoenix_integration.phoenix_tracer import traced
except ImportError:
    def traced(agent_name=None):
        def decorator(func):
            return func
        return decorator

logger = logging.getLogger(__name__)


@dataclass
class FieldFix:
    """Historical field fix from CMMS or interaction logs."""
    problem_description: str
    solution_applied: str
    technician_notes: str
    time_to_fix_hours: float
    parts_used: list[str]
    date: datetime
    source: str  # 'cmms_work_order', 'interaction_history', 'correction'
    success_confirmed: bool

    def to_dict(self) -> dict:
        """Convert to dict for serialization."""
        data = asdict(self)
        data['date'] = data['date'].isoformat()
        return data


class FieldFixRetriever:
    """
    Find historical fixes from CMMS work orders and interaction logs.

    Data sources:
    1. CMMS work orders (if integrations/atlas_cmms.py available)
    2. user_interactions table (Neon database)
    3. extraction_corrections table (technician corrections)

    Ranking algorithm:
    - Recency: Newer fixes score higher (decay over 180 days)
    - Similarity: Vector similarity to problem context (if provided)
    - Success: Confirmed fixes get +0.2 boost
    """

    def __init__(self):
        """Initialize FieldFixRetriever."""
        self.db = DatabaseManager()

        # Try to import Atlas CMMS integration
        try:
            from integrations.atlas_cmms import AtlasCMMSClient
            self.cmms_client = AtlasCMMSClient()
            logger.info("✅ Atlas CMMS integration available")
        except ImportError:
            self.cmms_client = None
            logger.info("⚠️  Atlas CMMS integration not available")

    @traced(agent_name="field_fix_retriever")
    async def get_field_fixes(
        self,
        model: str,
        problem_context: Optional[str] = None
    ) -> list[FieldFix]:
        """
        Get historical field fixes.

        Args:
            model: Equipment model
            problem_context: Optional problem description for similarity ranking

        Returns:
            List of FieldFix results (ranked, top 5)
        """
        logger.info(f"Getting field fixes for {model}")

        all_fixes = []

        try:
            # Step 1: Query CMMS work orders
            if self.cmms_client:
                cmms_fixes = await self.search_work_orders(model)
                all_fixes.extend(cmms_fixes)
                logger.info(f"Found {len(cmms_fixes)} CMMS work orders")

            # Step 2: Query interaction history
            interaction_fixes = await self.search_interaction_history(model)
            all_fixes.extend(interaction_fixes)
            logger.info(f"Found {len(interaction_fixes)} interaction history fixes")

            # Step 3: Query extraction corrections (technician gold data)
            correction_fixes = await self.search_corrections(model)
            all_fixes.extend(correction_fixes)
            logger.info(f"Found {len(correction_fixes)} correction fixes")

            # Step 4: Rank fixes
            if problem_context:
                ranked_fixes = await self.rank_fixes(all_fixes, problem_context)
            else:
                # Simple recency + success ranking
                ranked_fixes = sorted(
                    all_fixes,
                    key=lambda f: (f.success_confirmed, f.date),
                    reverse=True
                )

            return ranked_fixes[:5]  # Top 5

        except Exception as e:
            logger.error(f"Error getting field fixes: {e}", exc_info=True)
            return []

    async def search_work_orders(self, model: str) -> list[FieldFix]:
        """
        Query CMMS work orders.

        Args:
            model: Equipment model

        Returns:
            List of FieldFix from work orders
        """
        if not self.cmms_client:
            return []

        try:
            # Query CMMS API (placeholder - actual implementation depends on CMMS API)
            work_orders = await self.cmms_client.search_work_orders(
                equipment_model=model,
                status="completed",
                limit=10
            )

            fixes = []
            for wo in work_orders:
                fix = FieldFix(
                    problem_description=wo.get("problem", ""),
                    solution_applied=wo.get("solution", ""),
                    technician_notes=wo.get("notes", ""),
                    time_to_fix_hours=wo.get("hours_spent", 0.0),
                    parts_used=wo.get("parts", []),
                    date=datetime.fromisoformat(wo.get("completed_at", datetime.now().isoformat())),
                    source="cmms_work_order",
                    success_confirmed=wo.get("verified", False)
                )
                fixes.append(fix)

            return fixes

        except Exception as e:
            logger.warning(f"Error querying CMMS: {e}")
            return []

    async def search_interaction_history(self, model: str) -> list[FieldFix]:
        """
        Query user_interactions table.

        Args:
            model: Equipment model

        Returns:
            List of FieldFix from interactions
        """
        try:
            conn = self.db.get_connection()
            if not conn:
                logger.warning("No database connection")
                return []

            cursor = conn.cursor()

            # Query user_interactions where equipment matches
            sql = """
                SELECT
                    query_text,
                    response_text,
                    metadata,
                    created_at
                FROM user_interactions
                WHERE
                    metadata->>'equipment_model' ILIKE %s
                ORDER BY created_at DESC
                LIMIT 10
            """

            cursor.execute(sql, (f"%{model}%",))
            rows = cursor.fetchall()
            cursor.close()

            fixes = []
            for row in rows:
                metadata = row[2] or {}

                fix = FieldFix(
                    problem_description=row[0] or "",  # query_text
                    solution_applied=row[1] or "",  # response_text
                    technician_notes=metadata.get("notes", ""),
                    time_to_fix_hours=0.0,  # Not tracked in interactions
                    parts_used=[],
                    date=row[3] if isinstance(row[3], datetime) else datetime.fromisoformat(row[3]),
                    source="interaction_history",
                    success_confirmed=metadata.get("success", False)
                )
                fixes.append(fix)

            return fixes

        except Exception as e:
            logger.error(f"Error querying interactions: {e}", exc_info=True)
            return []

    async def search_corrections(self, model: str) -> list[FieldFix]:
        """
        Query extraction_corrections table (technician gold data).

        Args:
            model: Equipment model

        Returns:
            List of FieldFix from corrections
        """
        try:
            conn = self.db.get_connection()
            if not conn:
                return []

            cursor = conn.cursor()

            # Query extraction_corrections
            sql = """
                SELECT
                    original_extraction,
                    corrected_extraction,
                    technician_notes,
                    created_at
                FROM extraction_corrections
                WHERE
                    corrected_extraction->>'equipment_model' ILIKE %s
                ORDER BY created_at DESC
                LIMIT 10
            """

            cursor.execute(sql, (f"%{model}%",))
            rows = cursor.fetchall()
            cursor.close()

            fixes = []
            for row in rows:
                corrected = row[1] or {}

                fix = FieldFix(
                    problem_description=corrected.get("fault_description", ""),
                    solution_applied=corrected.get("solution", ""),
                    technician_notes=row[2] or "",
                    time_to_fix_hours=0.0,
                    parts_used=corrected.get("parts_used", []),
                    date=row[3] if isinstance(row[3], datetime) else datetime.fromisoformat(row[3]),
                    source="correction",
                    success_confirmed=True  # Corrections are always verified
                )
                fixes.append(fix)

            return fixes

        except Exception as e:
            logger.error(f"Error querying corrections: {e}", exc_info=True)
            return []

    async def rank_fixes(
        self,
        fixes: list[FieldFix],
        problem_context: str
    ) -> list[FieldFix]:
        """
        Rank fixes by relevance.

        Ranking algorithm:
        - Recency: max(0, 1 - (days_old / 180)) * 0.4
        - Similarity: cosine_similarity(problem, context) * 0.4
        - Success: +0.2 if success_confirmed

        Args:
            fixes: List of FieldFix
            problem_context: Problem description for similarity

        Returns:
            Sorted list of FieldFix
        """
        scored_fixes = []

        for fix in fixes:
            score = 0.0

            # Recency score (decay over 180 days)
            days_old = (datetime.now() - fix.date).days
            recency_score = max(0, 1 - (days_old / 180))
            score += recency_score * 0.4

            # Similarity score (simple word overlap for now)
            # In production, use embeddings + cosine similarity
            similarity = self._calculate_similarity(
                fix.problem_description,
                problem_context
            )
            score += similarity * 0.4

            # Success boost
            if fix.success_confirmed:
                score += 0.2

            scored_fixes.append((score, fix))

        # Sort by score descending
        scored_fixes.sort(key=lambda x: x[0], reverse=True)

        return [fix for score, fix in scored_fixes]

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate simple similarity (word overlap).

        In production, use:
        - text-embedding-3-small to generate embeddings
        - cosine similarity between vectors

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score 0-1
        """
        # Simple word overlap similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union) if union else 0.0

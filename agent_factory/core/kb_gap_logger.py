"""
KB Gap Logger - Tracks knowledge base gaps when Route C is triggered.

Logs queries that return 0 KB atoms to identify missing content,
detect patterns, and measure gap resolution over time.
"""
import json
import logging
from typing import Optional

from agent_factory.core.database_manager import DatabaseManager
from agent_factory.rivet_pro.models import RivetIntent, VendorType, EquipmentType

logger = logging.getLogger(__name__)


class KBGapLogger:
    """Logs and tracks knowledge base gaps."""

    def __init__(self, db: DatabaseManager):
        """
        Initialize KB gap logger.

        Args:
            db: DatabaseManager instance for executing queries
        """
        self.db = db

    def log_gap(
        self,
        query: str,
        intent: RivetIntent,
        search_filters: dict,
        user_id: Optional[str] = None
    ) -> int:
        """
        Log KB gap. Returns gap_id.
        Increments frequency if query seen before (within 7 days).

        Args:
            query: Original user query
            intent: Parsed RivetIntent with vendor, equipment, symptom
            search_filters: Filters used in KB search
            user_id: User identifier (Telegram user_id, etc.)

        Returns:
            gap_id: ID of the logged gap record
        """
        try:
            # Check if duplicate gap within 7 days
            check_sql = """
                SELECT id, frequency FROM kb_gaps
                WHERE query = %s AND triggered_at > NOW() - INTERVAL '7 days'
                AND resolved = FALSE
                ORDER BY triggered_at DESC LIMIT 1
            """
            result = self.db.execute_query(check_sql, (query,))

            if result:
                # Increment frequency for existing gap
                gap_id, freq = result[0]
                update_sql = """
                    UPDATE kb_gaps
                    SET frequency = %s, last_asked_at = NOW()
                    WHERE id = %s
                """
                self.db.execute_query(update_sql, (freq + 1, gap_id))
                logger.info(f"Incremented KB gap frequency: gap_id={gap_id}, frequency={freq + 1}")
                return gap_id
            else:
                # New gap - insert record
                insert_sql = """
                    INSERT INTO kb_gaps (
                        query, intent_vendor, intent_equipment,
                        intent_symptom, search_filters, user_id
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """
                result = self.db.execute_query(
                    insert_sql,
                    (
                        query,
                        intent.vendor.value if intent.vendor else None,
                        intent.equipment_type.value if intent.equipment_type else None,
                        intent.symptom,
                        json.dumps(search_filters),
                        user_id
                    )
                )
                gap_id = result[0][0]
                logger.info(f"Logged new KB gap: gap_id={gap_id}, query='{query[:50]}...'")
                return gap_id

        except Exception as e:
            logger.error(f"Failed to log KB gap: {e}", exc_info=True)
            # Return -1 to indicate failure (caller can check)
            return -1

    def mark_resolved(self, gap_id: int, atom_ids: list[str]) -> bool:
        """
        Mark gap as resolved after atoms ingested.

        Args:
            gap_id: ID of the gap to mark resolved
            atom_ids: List of atom IDs that resolved this gap

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            sql = """
                UPDATE kb_gaps
                SET resolved = TRUE, resolved_at = NOW(), resolution_atom_ids = %s
                WHERE id = %s
            """
            self.db.execute_query(sql, (atom_ids, gap_id))
            logger.info(f"Marked KB gap resolved: gap_id={gap_id}, atoms={len(atom_ids)}")
            return True
        except Exception as e:
            logger.error(f"Failed to mark gap resolved: {e}", exc_info=True)
            return False

    def get_top_gaps(self, limit: int = 10, resolved: bool = False) -> list[dict]:
        """
        Get top unresolved gaps by frequency.

        Args:
            limit: Maximum number of gaps to return
            resolved: If True, return resolved gaps; if False, return unresolved

        Returns:
            List of gap dictionaries with id, query, frequency, vendor, equipment
        """
        try:
            sql = """
                SELECT id, query, frequency, intent_vendor, intent_equipment, triggered_at, last_asked_at
                FROM kb_gaps
                WHERE resolved = %s
                ORDER BY frequency DESC, last_asked_at DESC
                LIMIT %s
            """
            result = self.db.execute_query(sql, (resolved, limit))
            return [
                {
                    "id": row[0],
                    "query": row[1],
                    "frequency": row[2],
                    "vendor": row[3],
                    "equipment": row[4],
                    "triggered_at": row[5].isoformat() if row[5] else None,
                    "last_asked_at": row[6].isoformat() if row[6] else None
                }
                for row in result
            ]
        except Exception as e:
            logger.error(f"Failed to get top gaps: {e}", exc_info=True)
            return []

    def get_gap_stats(self) -> dict:
        """
        Get overall KB gap statistics.

        Returns:
            Dictionary with total gaps, resolved count, resolution rate, avg frequency
        """
        try:
            sql = """
                SELECT
                    COUNT(*) as total_gaps,
                    COUNT(*) FILTER (WHERE resolved = TRUE) as resolved_count,
                    COUNT(*) FILTER (WHERE resolved = FALSE) as unresolved_count,
                    AVG(frequency) as avg_frequency,
                    AVG(EXTRACT(EPOCH FROM (resolved_at - triggered_at))/3600) as avg_resolution_hours
                FROM kb_gaps
            """
            result = self.db.execute_query(sql)
            if result:
                row = result[0]
                total = row[0] or 0
                resolved = row[1] or 0
                return {
                    "total_gaps": total,
                    "resolved_count": resolved,
                    "unresolved_count": row[2] or 0,
                    "resolution_rate": (resolved / total * 100) if total > 0 else 0.0,
                    "avg_frequency": float(row[3]) if row[3] else 0.0,
                    "avg_resolution_hours": float(row[4]) if row[4] else None
                }
            return {
                "total_gaps": 0,
                "resolved_count": 0,
                "unresolved_count": 0,
                "resolution_rate": 0.0,
                "avg_frequency": 0.0,
                "avg_resolution_hours": None
            }
        except Exception as e:
            logger.error(f"Failed to get gap stats: {e}", exc_info=True)
            return {}

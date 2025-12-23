"""
Database operations for Telegram Machine Library.

Provides CRUD operations for user machines and query history.
All operations are SYNCHRONOUS (not async) using DatabaseManager.
"""

import logging
from typing import Optional, List, Dict
from datetime import datetime

from agent_factory.core.database_manager import DatabaseManager

logger = logging.getLogger(__name__)


class MachineLibraryDB:
    """Database layer for machine library operations."""

    def __init__(self):
        """Initialize with DatabaseManager (multi-provider with failover)."""
        self.db = DatabaseManager()

    # ============================================================================
    # CREATE
    # ============================================================================

    def create_machine(self, user_id: str, machine_data: dict) -> str:
        """
        Create new machine for user.

        Args:
            user_id: Telegram user ID
            machine_data: Dict with keys: nickname (required), manufacturer,
                         model_number, serial_number, location, notes, photo_file_id

        Returns:
            machine_id (UUID as string)

        Raises:
            ValueError: If nickname already exists for this user
        """
        nickname = machine_data['nickname']

        # Check for duplicate nickname
        existing = self.db.execute_query(
            "SELECT id FROM user_machines WHERE user_id = %s AND nickname = %s",
            (user_id, nickname),
            fetch_mode="one"
        )

        if existing:
            raise ValueError(f"Machine '{nickname}' already exists in your library")

        # Insert new machine
        result = self.db.execute_query(
            """INSERT INTO user_machines
               (user_id, nickname, manufacturer, model_number, serial_number,
                location, notes, photo_file_id)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
               RETURNING id""",
            (
                user_id,
                nickname,
                machine_data.get('manufacturer'),
                machine_data.get('model_number'),
                machine_data.get('serial_number'),
                machine_data.get('location'),
                machine_data.get('notes'),
                machine_data.get('photo_file_id')
            ),
            fetch_mode="one"
        )

        machine_id = str(result[0])
        logger.info(f"Created machine {machine_id} for user {user_id}: {nickname}")
        return machine_id

    # ============================================================================
    # READ
    # ============================================================================

    def get_user_machines(self, user_id: str) -> List[Dict]:
        """
        Get all machines for user, ordered by most recently updated.

        Args:
            user_id: Telegram user ID

        Returns:
            List of machine dicts with keys: id, nickname, manufacturer,
            model_number, serial_number, location, notes, photo_file_id, last_queried
        """
        rows = self.db.execute_query(
            """SELECT id, nickname, manufacturer, model_number, serial_number,
                      location, notes, photo_file_id, last_queried
               FROM user_machines
               WHERE user_id = %s
               ORDER BY updated_at DESC""",
            (user_id,),
            fetch_mode="all"
        )

        if not rows:
            return []

        machines = []
        for row in rows:
            machines.append({
                'id': str(row[0]),
                'nickname': row[1],
                'manufacturer': row[2],
                'model_number': row[3],
                'serial_number': row[4],
                'location': row[5],
                'notes': row[6],
                'photo_file_id': row[7],
                'last_queried': row[8]
            })

        return machines

    def get_machine(self, machine_id: str) -> Optional[Dict]:
        """
        Get machine by ID.

        Args:
            machine_id: UUID of machine

        Returns:
            Machine dict or None if not found
        """
        result = self.db.execute_query(
            """SELECT id, user_id, nickname, manufacturer, model_number,
                      serial_number, location, notes, photo_file_id,
                      last_queried, created_at
               FROM user_machines
               WHERE id = %s""",
            (machine_id,),
            fetch_mode="one"
        )

        if not result:
            return None

        return {
            'id': str(result[0]),
            'user_id': result[1],
            'nickname': result[2],
            'manufacturer': result[3],
            'model_number': result[4],
            'serial_number': result[5],
            'location': result[6],
            'notes': result[7],
            'photo_file_id': result[8],
            'last_queried': result[9],
            'created_at': result[10]
        }

    def get_machine_by_nickname(self, user_id: str, nickname: str) -> Optional[Dict]:
        """
        Get machine by user_id and nickname.

        Args:
            user_id: Telegram user ID
            nickname: Machine nickname

        Returns:
            Machine dict or None if not found
        """
        result = self.db.execute_query(
            """SELECT id, user_id, nickname, manufacturer, model_number,
                      serial_number, location, notes, photo_file_id,
                      last_queried, created_at
               FROM user_machines
               WHERE user_id = %s AND nickname = %s""",
            (user_id, nickname),
            fetch_mode="one"
        )

        if not result:
            return None

        return {
            'id': str(result[0]),
            'user_id': result[1],
            'nickname': result[2],
            'manufacturer': result[3],
            'model_number': result[4],
            'serial_number': result[5],
            'location': result[6],
            'notes': result[7],
            'photo_file_id': result[8],
            'last_queried': result[9],
            'created_at': result[10]
        }

    # ============================================================================
    # UPDATE
    # ============================================================================

    def update_machine_last_queried(self, machine_id: str):
        """
        Update last_queried timestamp to NOW().

        Args:
            machine_id: UUID of machine
        """
        self.db.execute_query(
            "UPDATE user_machines SET last_queried = NOW() WHERE id = %s",
            (machine_id,),
            fetch_mode="none"
        )
        logger.debug(f"Updated last_queried for machine {machine_id}")

    def update_machine(self, machine_id: str, user_id: str, updates: Dict):
        """
        Update machine fields.

        Args:
            machine_id: UUID of machine
            user_id: Telegram user ID (for security validation)
            updates: Dict with keys to update (nickname, manufacturer, etc.)

        Raises:
            ValueError: If machine not found or doesn't belong to user
        """
        # Verify ownership
        machine = self.get_machine(machine_id)
        if not machine:
            raise ValueError("Machine not found")
        if machine['user_id'] != user_id:
            raise ValueError("Machine does not belong to user")

        # Build dynamic UPDATE query
        allowed_fields = ['nickname', 'manufacturer', 'model_number',
                         'serial_number', 'location', 'notes', 'photo_file_id']
        set_clauses = []
        params = []

        for field in allowed_fields:
            if field in updates:
                set_clauses.append(f"{field} = %s")
                params.append(updates[field])

        if not set_clauses:
            return  # Nothing to update

        params.append(machine_id)

        sql = f"""UPDATE user_machines
                  SET {', '.join(set_clauses)}
                  WHERE id = %s"""

        self.db.execute_query(sql, tuple(params), fetch_mode="none")
        logger.info(f"Updated machine {machine_id}: {list(updates.keys())}")

    # ============================================================================
    # DELETE
    # ============================================================================

    def delete_machine(self, machine_id: str, user_id: str):
        """
        Delete machine (cascades to history).

        Args:
            machine_id: UUID of machine
            user_id: Telegram user ID (for security validation)

        Raises:
            ValueError: If machine not found or doesn't belong to user
        """
        # Verify ownership before deleting
        machine = self.get_machine(machine_id)
        if not machine:
            raise ValueError("Machine not found")
        if machine['user_id'] != user_id:
            raise ValueError("Machine does not belong to user")

        self.db.execute_query(
            "DELETE FROM user_machines WHERE id = %s AND user_id = %s",
            (machine_id, user_id),
            fetch_mode="none"
        )
        logger.info(f"Deleted machine {machine_id} (user {user_id})")

    # ============================================================================
    # HISTORY
    # ============================================================================

    def add_query_history(
        self,
        machine_id: str,
        query_text: str,
        response_summary: str,
        route_taken: str,
        atoms_used: Optional[List[str]] = None
    ):
        """
        Log query to machine history.

        Args:
            machine_id: UUID of machine
            query_text: User's original query
            response_summary: First 500 chars of response
            route_taken: A, B, C, or D (RivetOrchestrator route)
            atoms_used: Optional list of knowledge atom IDs referenced
        """
        self.db.execute_query(
            """INSERT INTO user_machine_history
               (machine_id, query_text, response_summary, route_taken, atoms_used)
               VALUES (%s, %s, %s, %s, %s)""",
            (
                machine_id,
                query_text,
                response_summary[:500],  # Truncate to 500 chars
                route_taken,
                atoms_used or []
            ),
            fetch_mode="none"
        )
        logger.debug(f"Logged query history for machine {machine_id}: route {route_taken}")

    def get_machine_history(
        self,
        machine_id: str,
        limit: int = 10
    ) -> List[Dict]:
        """
        Get recent queries for machine.

        Args:
            machine_id: UUID of machine
            limit: Max number of queries to return (default 10)

        Returns:
            List of query dicts with keys: query, summary, route, timestamp, atoms_used
        """
        rows = self.db.execute_query(
            """SELECT query_text, response_summary, route_taken, created_at, atoms_used
               FROM user_machine_history
               WHERE machine_id = %s
               ORDER BY created_at DESC
               LIMIT %s""",
            (machine_id, limit),
            fetch_mode="all"
        )

        if not rows:
            return []

        history = []
        for row in rows:
            history.append({
                'query': row[0],
                'summary': row[1],
                'route': row[2],
                'timestamp': row[3],
                'atoms_used': row[4] or []
            })

        return history

    def get_query_count(self, machine_id: str) -> int:
        """
        Get total number of queries for machine.

        Args:
            machine_id: UUID of machine

        Returns:
            Query count
        """
        result = self.db.execute_query(
            "SELECT COUNT(*) FROM user_machine_history WHERE machine_id = %s",
            (machine_id,),
            fetch_mode="one"
        )
        return result[0] if result else 0

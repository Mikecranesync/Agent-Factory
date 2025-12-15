"""
Database adapter for RIVET Pro

Provides a unified interface for accessing RIVET Pro tables and functions
across different PostgreSQL providers (Neon, Supabase, Railway).

Usage:
    >>> from agent_factory.rivet_pro.database import RIVETProDatabase
    >>> db = RIVETProDatabase()  # Uses DATABASE_PROVIDER from .env
    >>> user = db.get_user('user_123')
    >>> db.increment_question_count('user_123')
"""

import os
import json
from typing import Optional, Dict, List, Any
from datetime import datetime

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()


class RIVETProDatabase:
    """
    Database adapter for RIVET Pro tables and functions.

    Supports multiple PostgreSQL providers with automatic connection management.
    """

    def __init__(self, provider: Optional[str] = None):
        """
        Initialize database connection.

        Args:
            provider: Database provider (neon, supabase, railway). If None, uses DATABASE_PROVIDER from .env
        """
        self.provider = provider or os.getenv("DATABASE_PROVIDER", "neon")
        self.conn = None
        self._connect()

    def _connect(self):
        """Establish database connection based on provider"""
        try:
            if self.provider == "neon":
                self.conn = psycopg2.connect(os.getenv("NEON_DB_URL"))
            elif self.provider == "supabase":
                self.conn = psycopg2.connect(
                    host=os.getenv("SUPABASE_DB_HOST"),
                    port=os.getenv("SUPABASE_DB_PORT", "5432"),
                    database=os.getenv("SUPABASE_DB_NAME", "postgres"),
                    user=os.getenv("SUPABASE_DB_USER", "postgres"),
                    password=os.getenv("SUPABASE_DB_PASSWORD"),
                )
            elif self.provider == "railway":
                self.conn = psycopg2.connect(os.getenv("RAILWAY_DB_URL"))
            else:
                raise ValueError(f"Unknown provider: {self.provider}")

            self.conn.autocommit = True  # Auto-commit for convenience
        except Exception as e:
            raise ConnectionError(f"Failed to connect to {self.provider}: {e}")

    def _execute(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Execute query and return results as list of dicts"""
        cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            cursor.execute(query, params)
            if cursor.description:  # SELECT query
                return [dict(row) for row in cursor.fetchall()]
            return []
        finally:
            cursor.close()

    def _execute_one(self, query: str, params: tuple = None) -> Optional[Dict[str, Any]]:
        """Execute query and return single result as dict"""
        cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            cursor.execute(query, params)
            if cursor.description:
                row = cursor.fetchone()
                return dict(row) if row else None
            return None
        finally:
            cursor.close()

    def _call_function(self, function_name: str, **kwargs) -> Any:
        """Call a PostgreSQL function with named parameters"""
        # Build parameter string
        param_names = list(kwargs.keys())
        param_values = list(kwargs.values())
        param_placeholders = ", ".join([f"{name} := %s" for name in param_names])

        query = f"SELECT {function_name}({param_placeholders})"
        cursor = self.conn.cursor()
        try:
            cursor.execute(query, param_values)
            result = cursor.fetchone()
            return result[0] if result else None
        finally:
            cursor.close()

    # =============================================================================
    # User Subscriptions
    # =============================================================================

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user subscription by user_id"""
        return self._execute_one(
            "SELECT * FROM user_subscriptions WHERE user_id = %s",
            (user_id,)
        )

    def get_user_by_telegram_id(self, telegram_user_id: int) -> Optional[Dict[str, Any]]:
        """Get user subscription by Telegram user ID"""
        return self._execute_one(
            "SELECT * FROM user_subscriptions WHERE telegram_user_id = %s",
            (telegram_user_id,)
        )

    def create_user(self, user_id: str, telegram_user_id: int, telegram_username: str, **kwargs) -> Dict[str, Any]:
        """Create new user subscription"""
        fields = ["user_id", "telegram_user_id", "telegram_username"]
        values = [user_id, telegram_user_id, telegram_username]

        for key, value in kwargs.items():
            fields.append(key)
            values.append(value)

        placeholders = ", ".join(["%s"] * len(values))
        field_names = ", ".join(fields)

        query = f"""
            INSERT INTO user_subscriptions ({field_names})
            VALUES ({placeholders})
            RETURNING *
        """
        return self._execute_one(query, tuple(values))

    def get_user_limits(self, user_id: str) -> Dict[str, Any]:
        """Get user limits using helper function"""
        result = self._call_function("get_user_limits", p_user_id=user_id)
        return json.loads(result) if result else {}

    def increment_question_count(self, user_id: str) -> Dict[str, Any]:
        """Increment user's daily question count"""
        result = self._call_function("increment_question_count", p_user_id=user_id)
        return json.loads(result) if result else {}

    # =============================================================================
    # Troubleshooting Sessions
    # =============================================================================

    def create_session(self, user_id: str, issue_description: str, **kwargs) -> Dict[str, Any]:
        """Create new troubleshooting session"""
        fields = ["user_id", "issue_description"]
        values = [user_id, issue_description]

        for key, value in kwargs.items():
            fields.append(key)
            values.append(value)

        placeholders = ", ".join(["%s"] * len(values))
        field_names = ", ".join(fields)

        query = f"""
            INSERT INTO troubleshooting_sessions ({field_names})
            VALUES ({placeholders})
            RETURNING *
        """
        return self._execute_one(query, tuple(values))

    def get_user_sessions(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user's recent troubleshooting sessions"""
        return self._execute(
            """
            SELECT * FROM troubleshooting_sessions
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (user_id, limit)
        )

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get troubleshooting session by ID"""
        return self._execute_one(
            "SELECT * FROM troubleshooting_sessions WHERE id = %s",
            (session_id,)
        )

    def update_session(self, session_id: str, **kwargs) -> Dict[str, Any]:
        """Update troubleshooting session"""
        set_clauses = [f"{key} = %s" for key in kwargs.keys()]
        values = list(kwargs.values())
        values.append(session_id)

        query = f"""
            UPDATE troubleshooting_sessions
            SET {", ".join(set_clauses)}
            WHERE id = %s
            RETURNING *
        """
        return self._execute_one(query, tuple(values))

    # =============================================================================
    # Expert Profiles & Bookings
    # =============================================================================

    def get_available_experts(self, specialty: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get available expert technicians"""
        result = self._call_function(
            "get_available_experts",
            p_specialty=specialty
        )
        return json.loads(result) if result else []

    def create_booking(self, user_id: str, expert_id: str, **kwargs) -> Dict[str, Any]:
        """Create new expert booking"""
        fields = ["user_id", "expert_id"]
        values = [user_id, expert_id]

        for key, value in kwargs.items():
            fields.append(key)
            values.append(value)

        placeholders = ", ".join(["%s"] * len(values))
        field_names = ", ".join(fields)

        query = f"""
            INSERT INTO expert_bookings ({field_names})
            VALUES ({placeholders})
            RETURNING *
        """
        return self._execute_one(query, tuple(values))

    # =============================================================================
    # Conversion Events
    # =============================================================================

    def track_conversion_event(
        self,
        user_id: str,
        event_type: str,
        converted: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """Track conversion funnel event"""
        fields = ["user_id", "event_type", "converted"]
        values = [user_id, event_type, converted]

        for key, value in kwargs.items():
            fields.append(key)
            values.append(value)

        placeholders = ", ".join(["%s"] * len(values))
        field_names = ", ".join(fields)

        query = f"""
            INSERT INTO conversion_events ({field_names})
            VALUES ({placeholders})
            RETURNING *
        """
        return self._execute_one(query, tuple(values))

    # =============================================================================
    # Analytics
    # =============================================================================

    def get_metrics(self, days: int = 30) -> Dict[str, Any]:
        """Get RIVET Pro platform metrics"""
        result = self._call_function("get_rivet_pro_metrics", p_days=days)
        return json.loads(result) if result else {}

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

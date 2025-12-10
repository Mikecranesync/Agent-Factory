"""
Memory storage backends for Agent Factory.

Provides abstract interface and implementations for persisting conversation history
and session data across different storage backends.

Implementations:
- InMemoryStorage: Fast, ephemeral storage (development/testing)
- SQLiteStorage: Local file-based persistence (single-user apps)
- SupabaseMemoryStorage: Cloud database storage (production/multi-user)

Example Usage:
    >>> from agent_factory.memory import Session, SupabaseMemoryStorage
    >>>
    >>> # Production: Use Supabase
    >>> storage = SupabaseMemoryStorage()
    >>> session = Session(user_id="alice", storage=storage)
    >>> session.add_user_message("My name is Alice")
    >>> session.save()  # Persists to Supabase
    >>>
    >>> # Development: Use in-memory
    >>> storage = InMemoryStorage()
    >>> session = Session(user_id="bob", storage=storage)
"""

import json
import os
import sqlite3
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class MemoryStorage(ABC):
    """
    Abstract base class for memory storage backends.

    All storage implementations must provide:
    - save_session(session) -> None
    - load_session(session_id) -> Optional[Session]
    - delete_session(session_id) -> bool
    - list_sessions(user_id) -> List[str]
    """

    @abstractmethod
    def save_session(self, session: Any) -> None:
        """
        Persist a session to storage.

        Args:
            session: Session instance to save
        """
        pass

    @abstractmethod
    def load_session(self, session_id: str) -> Optional[Any]:
        """
        Load a session from storage.

        Args:
            session_id: Unique session identifier

        Returns:
            Session instance or None if not found
        """
        pass

    @abstractmethod
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session from storage.

        Args:
            session_id: Unique session identifier

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    def list_sessions(self, user_id: Optional[str] = None) -> List[str]:
        """
        List all session IDs, optionally filtered by user.

        Args:
            user_id: Optional user ID filter

        Returns:
            List of session IDs
        """
        pass


class InMemoryStorage(MemoryStorage):
    """
    In-memory storage backend.

    Fast but ephemeral - data is lost when process ends.
    Suitable for development, testing, and short-lived sessions.

    Example:
        >>> storage = InMemoryStorage()
        >>> session = Session(user_id="alice", storage=storage)
        >>> session.save()
    """

    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def save_session(self, session: Any) -> None:
        """Save session to memory."""
        self._sessions[session.session_id] = session.to_dict()

    def load_session(self, session_id: str) -> Optional[Any]:
        """Load session from memory."""
        from agent_factory.memory.session import Session

        data = self._sessions.get(session_id)
        if data:
            return Session.from_dict(data, storage=self)
        return None

    def delete_session(self, session_id: str) -> bool:
        """Delete session from memory."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def list_sessions(self, user_id: Optional[str] = None) -> List[str]:
        """List all sessions, optionally filtered by user."""
        if user_id:
            return [
                sid for sid, data in self._sessions.items()
                if data.get("user_id") == user_id
            ]
        return list(self._sessions.keys())


class SQLiteStorage(MemoryStorage):
    """
    SQLite storage backend.

    Persistent file-based storage suitable for single-user applications.
    Lightweight, no external dependencies, stores data in local .db file.

    Example:
        >>> storage = SQLiteStorage("sessions.db")
        >>> session = Session(user_id="alice", storage=storage)
        >>> session.save()
    """

    def __init__(self, db_path: str = "sessions.db"):
        """
        Initialize SQLite storage.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                data TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_active TEXT NOT NULL
            )
        """)

        conn.commit()
        conn.close()

    def save_session(self, session: Any) -> None:
        """Save session to SQLite database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        data = session.to_dict()
        cursor.execute("""
            INSERT OR REPLACE INTO sessions (session_id, user_id, data, created_at, last_active)
            VALUES (?, ?, ?, ?, ?)
        """, (
            session.session_id,
            session.user_id,
            json.dumps(data),
            session.created_at.isoformat(),
            session.last_active.isoformat()
        ))

        conn.commit()
        conn.close()

    def load_session(self, session_id: str) -> Optional[Any]:
        """Load session from SQLite database."""
        from agent_factory.memory.session import Session

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT data FROM sessions WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            data = json.loads(row[0])
            return Session.from_dict(data, storage=self)
        return None

    def delete_session(self, session_id: str) -> bool:
        """Delete session from SQLite database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        deleted = cursor.rowcount > 0

        conn.commit()
        conn.close()

        return deleted

    def list_sessions(self, user_id: Optional[str] = None) -> List[str]:
        """List all sessions from SQLite database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if user_id:
            cursor.execute("SELECT session_id FROM sessions WHERE user_id = ?", (user_id,))
        else:
            cursor.execute("SELECT session_id FROM sessions")

        sessions = [row[0] for row in cursor.fetchall()]
        conn.close()

        return sessions


class SupabaseMemoryStorage(MemoryStorage):
    """
    Supabase PostgreSQL storage backend.

    Cloud-based persistent storage suitable for production multi-user applications.
    Provides:
    - Automatic backups
    - Multi-tenancy support
    - Fast queries with PostgreSQL
    - Real-time sync capabilities

    Environment Variables Required:
        SUPABASE_URL: Your Supabase project URL
        SUPABASE_KEY: Your Supabase API key (anon or service role)

    Example:
        >>> storage = SupabaseMemoryStorage()
        >>> session = Session(user_id="alice", storage=storage)
        >>> session.add_user_message("Hello")
        >>> session.save()  # Persists to Supabase cloud
    """

    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None
    ):
        """
        Initialize Supabase storage.

        Args:
            supabase_url: Supabase project URL (defaults to SUPABASE_URL env var)
            supabase_key: Supabase API key (defaults to SUPABASE_KEY env var)

        Raises:
            ValueError: If Supabase credentials not provided
            ImportError: If supabase-py package not installed
        """
        try:
            from supabase import create_client, Client
        except ImportError:
            raise ImportError(
                "Supabase storage requires 'supabase' package. "
                "Install with: pip install supabase"
            )

        # Get credentials from args or environment
        self.supabase_url = supabase_url or os.getenv("SUPABASE_URL")
        # Check multiple possible environment variable names for the key
        self.supabase_key = (
            supabase_key
            or os.getenv("SUPABASE_KEY")
            or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            or os.getenv("SUPABASE_ANON_KEY")
        )

        if not self.supabase_url or not self.supabase_key:
            raise ValueError(
                "Supabase credentials not found. "
                "Set SUPABASE_URL and SUPABASE_KEY (or SUPABASE_SERVICE_ROLE_KEY) environment variables or "
                "pass them to SupabaseMemoryStorage constructor."
            )

        # Initialize Supabase client
        self.client: Client = create_client(self.supabase_url, self.supabase_key)
        self.table_name = "session_memories"

    def save_session(self, session: Any) -> None:
        """
        Save session to Supabase.

        Stores session as multiple memory atoms:
        - One 'session_metadata' atom with session info
        - Individual atoms for each message

        Args:
            session: Session instance to save
        """
        from agent_factory.memory.session import Session

        # Save session metadata
        metadata_atom = {
            "session_id": session.session_id,
            "user_id": session.user_id,
            "memory_type": "session_metadata",
            "content": {
                "created_at": session.created_at.isoformat(),
                "last_active": session.last_active.isoformat(),
                "metadata": session.metadata,
                "message_count": len(session.history)
            },
            "created_at": datetime.now().isoformat()
        }

        # Delete old metadata then insert new (simpler than upsert with partial index)
        self.client.table(self.table_name).delete().eq(
            "session_id", session.session_id
        ).eq(
            "memory_type", "session_metadata"
        ).execute()

        # Insert fresh metadata
        self.client.table(self.table_name).insert(metadata_atom).execute()

        # Save messages as individual atoms
        for idx, message in enumerate(session.history.get_messages()):
            message_atom = {
                "session_id": session.session_id,
                "user_id": session.user_id,
                "memory_type": f"message_{message.role}",
                "content": {
                    "role": message.role,
                    "content": message.content,
                    "timestamp": message.timestamp.isoformat(),
                    "metadata": message.metadata or {},
                    "message_index": idx
                },
                "created_at": message.timestamp.isoformat()
            }

            self.client.table(self.table_name).insert(message_atom).execute()

    def load_session(self, session_id: str) -> Optional[Any]:
        """
        Load session from Supabase.

        Args:
            session_id: Unique session identifier

        Returns:
            Session instance or None if not found
        """
        from agent_factory.memory.session import Session
        from agent_factory.memory.history import MessageHistory, Message

        # Load session metadata
        response = self.client.table(self.table_name).select("*").eq(
            "session_id", session_id
        ).eq(
            "memory_type", "session_metadata"
        ).execute()

        if not response.data:
            return None

        metadata = response.data[0]

        # Load messages
        messages_response = self.client.table(self.table_name).select("*").eq(
            "session_id", session_id
        ).like(
            "memory_type", "message_%"
        ).order("created_at").execute()

        # Reconstruct message history
        history = MessageHistory()
        for msg_atom in messages_response.data:
            content = msg_atom["content"]
            history.add_message(
                role=content["role"],
                content=content["content"],
                metadata=content.get("metadata")
            )

        # Reconstruct session
        session = Session(
            session_id=session_id,
            user_id=metadata["user_id"],
            history=history,
            metadata=metadata["content"].get("metadata", {}),
            created_at=datetime.fromisoformat(metadata["content"]["created_at"]),
            last_active=datetime.fromisoformat(metadata["content"]["last_active"]),
            storage=self
        )

        return session

    def delete_session(self, session_id: str) -> bool:
        """
        Delete session from Supabase.

        Removes all memory atoms associated with the session.

        Args:
            session_id: Unique session identifier

        Returns:
            True if deleted, False if not found
        """
        response = self.client.table(self.table_name).delete().eq(
            "session_id", session_id
        ).execute()

        return len(response.data) > 0

    def list_sessions(self, user_id: Optional[str] = None) -> List[str]:
        """
        List all sessions from Supabase.

        Args:
            user_id: Optional user ID filter

        Returns:
            List of session IDs
        """
        query = self.client.table(self.table_name).select("session_id").eq(
            "memory_type", "session_metadata"
        )

        if user_id:
            query = query.eq("user_id", user_id)

        response = query.execute()

        return [row["session_id"] for row in response.data]

    def save_memory_atom(
        self,
        session_id: str,
        user_id: str,
        memory_type: str,
        content: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Save a custom memory atom to Supabase.

        Useful for saving specific types of session context like:
        - 'context': Project status updates
        - 'action': Tasks and next actions
        - 'issue': Bugs and problems
        - 'decision': Technical decisions
        - 'log': Development activities

        Args:
            session_id: Session identifier
            user_id: User identifier
            memory_type: Type of memory ('context', 'action', 'issue', 'decision', 'log')
            content: Memory content as dictionary
            metadata: Optional metadata

        Returns:
            Saved memory atom

        Example:
            >>> storage.save_memory_atom(
            ...     session_id="session_abc123",
            ...     user_id="alice",
            ...     memory_type="decision",
            ...     content={
            ...         "title": "Use Supabase for memory storage",
            ...         "rationale": "10x faster than file I/O",
            ...         "date": "2025-12-09"
            ...     }
            ... )
        """
        atom = {
            "session_id": session_id,
            "user_id": user_id,
            "memory_type": memory_type,
            "content": content,
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat()
        }

        response = self.client.table(self.table_name).insert(atom).execute()
        return response.data[0]

    def query_memory_atoms(
        self,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        memory_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Query memory atoms with filters.

        Args:
            session_id: Optional session ID filter
            user_id: Optional user ID filter
            memory_type: Optional memory type filter
            limit: Maximum number of results

        Returns:
            List of memory atoms matching filters

        Example:
            >>> # Get all decisions from last session
            >>> atoms = storage.query_memory_atoms(
            ...     session_id="session_abc123",
            ...     memory_type="decision"
            ... )
        """
        query = self.client.table(self.table_name).select("*")

        if session_id:
            query = query.eq("session_id", session_id)
        if user_id:
            query = query.eq("user_id", user_id)
        if memory_type:
            query = query.eq("memory_type", memory_type)

        response = query.order("created_at", desc=True).limit(limit).execute()
        return response.data

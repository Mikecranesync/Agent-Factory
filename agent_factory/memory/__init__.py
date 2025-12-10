"""
Memory & State Management for Agent Factory.

This module provides conversation memory, session management, and context handling
for multi-turn interactions. Essential for Friday (voice AI) and Jarvis (ecosystem manager).

Core Components:
- Message: Individual message in a conversation
- MessageHistory: Manages conversation history
- Session: User conversation session with persistence
- MemoryStorage: Abstract storage backend
- InMemoryStorage: In-memory storage (development)
- SQLiteStorage: SQLite persistence (production)
- ContextManager: Context window management

Example Usage:
    >>> from agent_factory.memory import Session, SQLiteStorage
    >>>
    >>> # Create session with persistence
    >>> storage = SQLiteStorage("sessions.db")
    >>> session = Session(user_id="alice", storage=storage)
    >>>
    >>> # Add messages
    >>> session.add_user_message("My name is Alice")
    >>> session.add_assistant_message("Nice to meet you, Alice!")
    >>>
    >>> # Save and reload
    >>> session.save()
    >>> loaded = Session.load(session.session_id, storage=storage)
    >>> print(loaded.get_full_context())  # History restored
"""

from agent_factory.memory.history import Message, MessageHistory
from agent_factory.memory.session import Session
from agent_factory.memory.storage import (
    MemoryStorage,
    InMemoryStorage,
    SQLiteStorage,
    SupabaseMemoryStorage,
)
from agent_factory.memory.context_manager import ContextManager

__all__ = [
    "Message",
    "MessageHistory",
    "Session",
    "MemoryStorage",
    "InMemoryStorage",
    "SQLiteStorage",
    "SupabaseMemoryStorage",
    "ContextManager",
]

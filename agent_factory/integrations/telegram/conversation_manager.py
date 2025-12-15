"""
Conversation Manager for Telegram Bot

Manages multi-turn conversations with context awareness, enabling the bot to:
- Remember previous messages
- Reference past topics
- Maintain conversation state
- Learn from interactions

Part of Phase 1: Natural Language Evolution
"""

import json
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

from agent_factory.memory import Session, Message, MessageHistory
from agent_factory.rivet_pro.database import RIVETProDatabase


@dataclass
class ConversationContext:
    """
    Extracted context from conversation history.

    Provides structured information about what's been discussed.
    """
    last_topic: Optional[str] = None
    last_equipment_type: Optional[str] = None
    last_intent_type: Optional[str] = None
    mentioned_equipment: List[str] = None
    unresolved_issues: List[str] = None
    follow_up_count: int = 0

    def __post_init__(self):
        if self.mentioned_equipment is None:
            self.mentioned_equipment = []
        if self.unresolved_issues is None:
            self.unresolved_issues = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationContext":
        """Load from dictionary"""
        return cls(**data)


class ConversationManager:
    """
    Manages conversation sessions for Telegram users.

    Features:
    - Session persistence across bot restarts
    - Conversation history with context window
    - Context extraction for intelligent responses
    - Automatic session cleanup (old sessions)

    Usage:
        >>> manager = ConversationManager()
        >>> session = manager.get_or_create_session(user_id="123")
        >>> manager.add_user_message(session, "Motor running hot")
        >>> manager.add_bot_message(session, "Let me help diagnose that...")
        >>> context = manager.get_context(session)
        >>> print(context.last_topic)  # "motor overheating"
    """

    def __init__(self, db: Optional[RIVETProDatabase] = None):
        """
        Initialize conversation manager.

        Args:
            db: Database instance. If None, creates new connection.
        """
        self.db = db or RIVETProDatabase()
        self.active_sessions: Dict[str, Session] = {}  # In-memory cache
        self.context_window_size = 10  # Last N messages to include in context

    def get_or_create_session(self, user_id: str, telegram_username: Optional[str] = None) -> Session:
        """
        Get existing session or create new one for user.

        Args:
            user_id: Telegram user ID (as string)
            telegram_username: Optional username for new sessions

        Returns:
            Session instance with conversation history
        """
        # Check in-memory cache first
        if user_id in self.active_sessions:
            session = self.active_sessions[user_id]
            session.last_active = datetime.now()
            return session

        # Try to load from database
        session = self._load_session_from_db(user_id)

        if session is None:
            # Create new session
            session = Session(
                user_id=user_id,
                metadata={
                    "telegram_username": telegram_username,
                    "created_via": "telegram_bot",
                    "platform": "telegram"
                }
            )

        # Cache it
        self.active_sessions[user_id] = session
        return session

    def add_user_message(
        self,
        session: Session,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """
        Add user message to session.

        Args:
            session: Conversation session
            content: Message text from user
            metadata: Optional metadata (intent, equipment info, etc.)

        Returns:
            Created Message object
        """
        msg = session.add_user_message(content, metadata)
        self._update_context(session)
        return msg

    def add_bot_message(
        self,
        session: Session,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """
        Add bot response message to session.

        Args:
            session: Conversation session
            content: Bot's response text
            metadata: Optional metadata (confidence, atoms used, etc.)

        Returns:
            Created Message object
        """
        msg = session.add_assistant_message(content, metadata)
        return msg

    def get_context(self, session: Session) -> ConversationContext:
        """
        Extract structured context from conversation history.

        Analyzes recent messages to understand:
        - What was last discussed
        - Equipment mentioned
        - Unresolved issues
        - Follow-up patterns

        Args:
            session: Conversation session

        Returns:
            ConversationContext with extracted information
        """
        # Get recent messages
        recent_messages = session.history.get_messages(limit=self.context_window_size)

        if not recent_messages:
            return ConversationContext()

        # Extract context from messages
        context = ConversationContext()

        for msg in recent_messages:
            if msg.role == "user":
                # Extract equipment mentions
                equipment_keywords = ["motor", "vfd", "plc", "conveyor", "pump", "valve", "sensor"]
                for keyword in equipment_keywords:
                    if keyword in msg.content.lower() and keyword not in context.mentioned_equipment:
                        context.mentioned_equipment.append(keyword)

                # Check for follow-up indicators
                follow_up_phrases = ["what about", "tell me more", "can you explain", "how do i", "also"]
                if any(phrase in msg.content.lower() for phrase in follow_up_phrases):
                    context.follow_up_count += 1

            # Get metadata from messages
            if msg.metadata:
                if "intent_type" in msg.metadata:
                    context.last_intent_type = msg.metadata["intent_type"]
                if "equipment_type" in msg.metadata:
                    context.last_equipment_type = msg.metadata["equipment_type"]
                if "topic" in msg.metadata:
                    context.last_topic = msg.metadata["topic"]

        # Last user message is current topic
        last_user_msgs = [m for m in recent_messages if m.role == "user"]
        if last_user_msgs:
            last_content = last_user_msgs[-1].content
            # Simple topic extraction (first few words)
            words = last_content.lower().split()[:5]
            context.last_topic = " ".join(words)

        return context

    def get_context_window(self, session: Session, n: Optional[int] = None) -> List[Message]:
        """
        Get last N messages for context.

        Args:
            session: Conversation session
            n: Number of messages. If None, uses context_window_size

        Returns:
            List of recent messages
        """
        limit = n or self.context_window_size
        return session.history.get_messages(limit=limit)

    def get_context_summary(self, session: Session) -> str:
        """
        Generate natural language summary of conversation context.

        Useful for passing to LLM for context-aware responses.

        Args:
            session: Conversation session

        Returns:
            Human-readable context summary
        """
        context = self.get_context(session)
        recent_messages = self.get_context_window(session, n=5)

        summary_parts = []

        # Conversation length
        total_messages = len(session.history.messages)
        if total_messages > 0:
            summary_parts.append(f"Conversation has {total_messages} messages.")

        # Recent topic
        if context.last_topic:
            summary_parts.append(f"User is asking about: {context.last_topic}")

        # Equipment context
        if context.mentioned_equipment:
            equipment_str = ", ".join(context.mentioned_equipment)
            summary_parts.append(f"Equipment mentioned: {equipment_str}")

        # Follow-up indicator
        if context.follow_up_count > 0:
            summary_parts.append(f"This is a follow-up question (count: {context.follow_up_count})")

        # Recent exchange
        if recent_messages:
            summary_parts.append("\nRecent exchange:")
            for msg in recent_messages[-3:]:  # Last 3 messages
                role = "User" if msg.role == "user" else "Bot"
                content_preview = msg.content[:80] + "..." if len(msg.content) > 80 else msg.content
                summary_parts.append(f"{role}: {content_preview}")

        return "\n".join(summary_parts) if summary_parts else "No previous conversation context."

    def save_session(self, session: Session) -> bool:
        """
        Persist session to database.

        Args:
            session: Session to save

        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert session to storable format
            session_data = {
                "session_id": session.session_id,
                "user_id": session.user_id,
                "telegram_user_id": int(session.user_id) if session.user_id.isdigit() else None,
                "messages": json.dumps([
                    {
                        "role": msg.role,
                        "content": msg.content,
                        "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
                        "metadata": msg.metadata
                    }
                    for msg in session.history.messages
                ]),
                "context_summary": self.get_context_summary(session),
                "last_topic": self.get_context(session).last_topic,
                "updated_at": datetime.now()
            }

            # Check if session exists
            existing = self.db._execute_one(
                "SELECT session_id FROM conversation_sessions WHERE user_id = %s",
                (session.user_id,)
            )

            if existing:
                # Update existing
                self.db._execute(
                    """
                    UPDATE conversation_sessions
                    SET messages = %s, context_summary = %s, last_topic = %s, updated_at = %s
                    WHERE user_id = %s
                    """,
                    (
                        session_data["messages"],
                        session_data["context_summary"],
                        session_data["last_topic"],
                        session_data["updated_at"],
                        session.user_id
                    )
                )
            else:
                # Insert new
                self.db._execute(
                    """
                    INSERT INTO conversation_sessions
                    (session_id, user_id, telegram_user_id, messages, context_summary, last_topic)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        session_data["session_id"],
                        session_data["user_id"],
                        session_data["telegram_user_id"],
                        session_data["messages"],
                        session_data["context_summary"],
                        session_data["last_topic"]
                    )
                )

            return True

        except Exception as e:
            print(f"Error saving session: {e}")
            return False

    def _load_session_from_db(self, user_id: str) -> Optional[Session]:
        """Load session from database"""
        try:
            row = self.db._execute_one(
                "SELECT * FROM conversation_sessions WHERE user_id = %s",
                (user_id,)
            )

            if not row:
                return None

            # Reconstruct session
            messages_data = json.loads(row["messages"])
            history = MessageHistory()

            for msg_data in messages_data:
                msg = Message(
                    role=msg_data["role"],
                    content=msg_data["content"],
                    timestamp=datetime.fromisoformat(msg_data["timestamp"]) if msg_data.get("timestamp") else None,
                    metadata=msg_data.get("metadata")
                )
                history.messages.append(msg)

            session = Session(
                session_id=row["session_id"],
                user_id=row["user_id"],
                history=history,
                metadata={
                    "loaded_from_db": True,
                    "last_topic": row.get("last_topic")
                },
                created_at=row["created_at"],
                last_active=row["updated_at"]
            )

            return session

        except Exception as e:
            print(f"Error loading session: {e}")
            return None

    def _update_context(self, session: Session):
        """Update session metadata with current context"""
        context = self.get_context(session)
        session.metadata["context"] = context.to_dict()
        session.metadata["last_update"] = datetime.now().isoformat()

    def cleanup_old_sessions(self, days: int = 30):
        """
        Remove sessions older than N days.

        Args:
            days: Age threshold in days
        """
        try:
            cutoff = datetime.now() - timedelta(days=days)
            self.db._execute(
                "DELETE FROM conversation_sessions WHERE updated_at < %s",
                (cutoff,)
            )
            # Also clear from memory cache
            expired_users = [
                user_id for user_id, session in self.active_sessions.items()
                if session.last_active < cutoff
            ]
            for user_id in expired_users:
                del self.active_sessions[user_id]

        except Exception as e:
            print(f"Error cleaning up sessions: {e}")

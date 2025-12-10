"""
Conversation history management for Agent Factory.

Provides:
- Message class for individual messages
- MessageHistory class for managing conversation threads
- Token counting and context window management

Example Usage:
    >>> from agent_factory.memory import MessageHistory
    >>>
    >>> history = MessageHistory()
    >>> history.add_message("user", "What is Python?")
    >>> history.add_message("assistant", "Python is a programming language.")
    >>> print(len(history))  # 2
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional


@dataclass
class Message:
    """
    Individual message in a conversation.

    Attributes:
        role: Message sender ('user', 'assistant', 'system')
        content: Message content
        timestamp: When message was created
        metadata: Optional message metadata (tokens, cost, etc.)
    """

    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert message to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata or {}
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """
        Create message from dictionary.

        Args:
            data: Dictionary data

        Returns:
            Message instance
        """
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata")
        )

    def __repr__(self) -> str:
        """String representation."""
        preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"Message(role={self.role}, content='{preview}')"


class MessageHistory:
    """
    Manages conversation history with context window support.

    Features:
    - Add messages by role
    - Get messages with optional limits
    - Clear history
    - Token counting for context windows
    - Export to LangChain/OpenAI format

    Example:
        >>> history = MessageHistory()
        >>> history.add_message("user", "Hello")
        >>> history.add_message("assistant", "Hi there!")
        >>> messages = history.get_messages()
        >>> print(len(messages))  # 2
    """

    def __init__(self):
        """Initialize empty message history."""
        self._messages: List[Message] = []

    def add_message(
        self,
        role: Literal["user", "assistant", "system"],
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """
        Add a message to history.

        Args:
            role: Message sender
            content: Message content
            metadata: Optional metadata

        Returns:
            The created Message object
        """
        message = Message(
            role=role,
            content=content,
            metadata=metadata
        )
        self._messages.append(message)
        return message

    def get_messages(
        self,
        limit: Optional[int] = None,
        role: Optional[Literal["user", "assistant", "system"]] = None
    ) -> List[Message]:
        """
        Get messages from history.

        Args:
            limit: Optional limit on number of messages (most recent)
            role: Optional filter by role

        Returns:
            List of messages
        """
        messages = self._messages

        # Filter by role if specified
        if role:
            messages = [m for m in messages if m.role == role]

        # Apply limit if specified
        if limit:
            messages = messages[-limit:]

        return messages

    def get_context_window(
        self,
        max_tokens: int,
        token_counter: Optional[Any] = None
    ) -> List[Message]:
        """
        Get messages that fit within token limit.

        Args:
            max_tokens: Maximum tokens allowed
            token_counter: Optional custom token counter function

        Returns:
            List of messages within token limit (most recent first)
        """
        if not token_counter:
            # Simple character-based estimation (1 token ≈ 4 characters)
            token_counter = lambda msg: len(msg.content) // 4

        # Start from most recent and work backwards
        messages = []
        total_tokens = 0

        for message in reversed(self._messages):
            msg_tokens = token_counter(message)

            if total_tokens + msg_tokens <= max_tokens:
                messages.insert(0, message)
                total_tokens += msg_tokens
            else:
                break

        return messages

    def clear(self) -> None:
        """Clear all messages from history."""
        self._messages.clear()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert history to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "messages": [msg.to_dict() for msg in self._messages]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MessageHistory":
        """
        Create history from dictionary.

        Args:
            data: Dictionary data

        Returns:
            MessageHistory instance
        """
        history = cls()
        for msg_data in data.get("messages", []):
            msg = Message.from_dict(msg_data)
            history._messages.append(msg)
        return history

    def to_langchain_format(self) -> List[Dict[str, str]]:
        """
        Export to LangChain message format.

        Returns:
            List of dicts with 'role' and 'content' keys

        Example:
            >>> history.to_langchain_format()
            [{'role': 'user', 'content': 'Hello'}, ...]
        """
        return [
            {"role": msg.role, "content": msg.content}
            for msg in self._messages
        ]

    def to_openai_format(self) -> List[Dict[str, str]]:
        """
        Export to OpenAI message format.

        Returns:
            List of dicts with 'role' and 'content' keys

        Example:
            >>> history.to_openai_format()
            [{'role': 'user', 'content': 'Hello'}, ...]
        """
        return self.to_langchain_format()  # Same format

    def __len__(self) -> int:
        """Return number of messages in history."""
        return len(self._messages)

    def __repr__(self) -> str:
        """String representation."""
        return f"MessageHistory({len(self._messages)} messages)"

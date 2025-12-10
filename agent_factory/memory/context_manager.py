"""
Context window management for LLM conversations.

Handles token limits, message truncation, and context compression
to fit conversations within model token windows.

Example Usage:
    >>> from agent_factory.memory import ContextManager, MessageHistory
    >>>
    >>> history = MessageHistory()
    >>> history.add_message("user", "Hello" * 1000)  # Long message
    >>>
    >>> manager = ContextManager(max_tokens=1000)
    >>> messages = manager.fit_to_window(history)
    >>> print(len(messages))  # Only messages that fit in 1000 tokens
"""

from typing import Any, Callable, List, Optional

from agent_factory.memory.history import Message, MessageHistory


class ContextManager:
    """
    Manages conversation context windows for LLM token limits.

    Features:
    - Token counting with configurable counter
    - Message truncation to fit token windows
    - Preserve system messages
    - Keep most recent messages

    Example:
        >>> manager = ContextManager(max_tokens=4000)
        >>> messages = manager.fit_to_window(history)
    """

    def __init__(
        self,
        max_tokens: int = 4000,
        token_counter: Optional[Callable[[Message], int]] = None,
        preserve_system: bool = True
    ):
        """
        Initialize context manager.

        Args:
            max_tokens: Maximum tokens for context window
            token_counter: Optional custom token counter function
            preserve_system: Always include system messages
        """
        self.max_tokens = max_tokens
        self.preserve_system = preserve_system

        # Default token counter (rough estimate: 1 token ≈ 4 characters)
        if token_counter is None:
            token_counter = lambda msg: len(msg.content) // 4 + 4  # +4 for role overhead

        self.token_counter = token_counter

    def count_tokens(self, messages: List[Message]) -> int:
        """
        Count total tokens in message list.

        Args:
            messages: List of messages

        Returns:
            Total token count
        """
        return sum(self.token_counter(msg) for msg in messages)

    def fit_to_window(
        self,
        history: MessageHistory,
        reserve_tokens: int = 0
    ) -> List[Message]:
        """
        Fit message history to token window.

        Keeps most recent messages that fit within max_tokens.
        System messages are always preserved if preserve_system=True.

        Args:
            history: Message history to fit
            reserve_tokens: Tokens to reserve for response

        Returns:
            List of messages that fit in token window

        Example:
            >>> manager = ContextManager(max_tokens=1000)
            >>> messages = manager.fit_to_window(history, reserve_tokens=500)
            >>> # Returns messages using at most 500 tokens (reserving 500 for response)
        """
        available_tokens = self.max_tokens - reserve_tokens
        all_messages = history.get_messages()

        if not all_messages:
            return []

        # Separate system and non-system messages
        system_messages = [m for m in all_messages if m.role == "system"]
        other_messages = [m for m in all_messages if m.role != "system"]

        # Always include system messages if preserve_system=True
        result = []
        tokens_used = 0

        if self.preserve_system and system_messages:
            result.extend(system_messages)
            tokens_used = self.count_tokens(system_messages)

        # Add other messages from most recent backwards
        for message in reversed(other_messages):
            msg_tokens = self.token_counter(message)

            if tokens_used + msg_tokens <= available_tokens:
                result.insert(len(system_messages), message)  # Insert after system messages
                tokens_used += msg_tokens
            else:
                break

        return result

    def truncate_message(
        self,
        message: Message,
        max_tokens: int,
        suffix: str = "..."
    ) -> Message:
        """
        Truncate a single message to fit token limit.

        Args:
            message: Message to truncate
            max_tokens: Maximum tokens allowed
            suffix: Suffix to add to truncated content

        Returns:
            Truncated message (or original if it fits)

        Example:
            >>> manager = ContextManager()
            >>> long_msg = Message(role="user", content="Hello" * 1000)
            >>> short_msg = manager.truncate_message(long_msg, max_tokens=50)
        """
        current_tokens = self.token_counter(message)

        if current_tokens <= max_tokens:
            return message

        # Estimate characters needed (rough: 4 chars per token)
        target_chars = max_tokens * 4 - len(suffix)
        truncated_content = message.content[:target_chars] + suffix

        return Message(
            role=message.role,
            content=truncated_content,
            timestamp=message.timestamp,
            metadata=message.metadata
        )

    def summarize_old_messages(
        self,
        messages: List[Message],
        summary_prompt: str = "Summarize the above conversation concisely."
    ) -> str:
        """
        Create a summary of old messages to save tokens.

        Placeholder for future LLM-based summarization.

        Args:
            messages: Messages to summarize
            summary_prompt: Prompt for summarization

        Returns:
            Summary string (placeholder implementation)
        """
        # Simple placeholder: just count messages
        # In production, you'd use an LLM to generate actual summary
        user_count = sum(1 for m in messages if m.role == "user")
        assistant_count = sum(1 for m in messages if m.role == "assistant")

        return (
            f"[Previous conversation: {user_count} user messages, "
            f"{assistant_count} assistant messages]"
        )

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.

        Args:
            text: Text to estimate

        Returns:
            Estimated token count
        """
        # Simple estimation: 1 token ≈ 4 characters
        return len(text) // 4

    def __repr__(self) -> str:
        """String representation."""
        return f"ContextManager(max_tokens={self.max_tokens})"

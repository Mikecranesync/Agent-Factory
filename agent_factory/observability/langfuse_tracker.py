"""
LangFuse Tracker - Observability for LangGraph Workflows

Provides LangFuse integration for tracking multi-agent workflows:
- Visual workflow traces
- Cost tracking per query
- Quality score monitoring
- Shareable trace links

Usage:
    from agent_factory.observability import LangFuseTracker

    tracker = LangFuseTracker()
    callback = tracker.get_callback()

    # Use callback with agents
    agent = factory.create_agent(..., callbacks=[callback])

    # Get trace link after workflow
    trace_link = tracker.get_trace_link()
"""

import os
from typing import Optional
from langfuse.langchain import CallbackHandler


class LangFuseTracker:
    """
    LangFuse integration for multi-agent workflow observability.

    Automatically configures from environment variables:
    - LANGFUSE_SECRET_KEY
    - LANGFUSE_PUBLIC_KEY
    - LANGFUSE_BASE_URL (optional, defaults to cloud)

    Example:
        >>> tracker = LangFuseTracker()
        >>> callback = tracker.get_callback()
        >>>
        >>> # Use with agent
        >>> agent = factory.create_agent(
        ...     role="Researcher",
        ...     callbacks=[callback]
        ... )
        >>>
        >>> # After workflow executes
        >>> trace_link = tracker.get_trace_link()
        >>> print(f"View trace: {trace_link}")
    """

    def __init__(self):
        """
        Initialize LangFuse tracker with configuration from .env

        Raises:
            ValueError: If LangFuse keys not configured
        """
        # Load configuration
        self.secret_key = os.getenv("LANGFUSE_SECRET_KEY")
        self.public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
        self.base_url = os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com")

        # Validate configuration
        if not self.secret_key or not self.public_key:
            raise ValueError(
                "LangFuse not configured. Add to .env:\n"
                "  LANGFUSE_SECRET_KEY=sk-lf-...\n"
                "  LANGFUSE_PUBLIC_KEY=pk-lf-...\n"
                "  LANGFUSE_BASE_URL=https://cloud.langfuse.com  # optional"
            )

        # Initialize callback handler
        self._callback = None
        self._latest_trace_id = None

    def get_callback(self, session_id: Optional[str] = None, user_id: Optional[str] = None) -> CallbackHandler:
        """
        Get LangFuse callback handler for agent.

        Args:
            session_id: Optional session identifier
            user_id: Optional user identifier

        Returns:
            CallbackHandler ready to use with LangChain agents

        Example:
            >>> tracker = LangFuseTracker()
            >>> callback = tracker.get_callback(
            ...     session_id="sess_123",
            ...     user_id="user_456"
            ... )
            >>> agent = factory.create_agent(..., callbacks=[callback])
        """
        self._callback = CallbackHandler(
            secret_key=self.secret_key,
            public_key=self.public_key,
            host=self.base_url,
            session_id=session_id,
            user_id=user_id
        )

        return self._callback

    def get_trace_link(self) -> Optional[str]:
        """
        Get URL to view the latest trace in LangFuse dashboard.

        Returns:
            URL string or None if no trace available

        Example:
            >>> tracker = LangFuseTracker()
            >>> callback = tracker.get_callback()
            >>>
            >>> # ... workflow executes ...
            >>>
            >>> link = tracker.get_trace_link()
            >>> print(f"View detailed trace: {link}")
        """
        if not self._callback:
            return None

        # Flush to ensure trace is uploaded
        self._callback.flush()

        # Get trace ID from callback (if available)
        # Note: LangFuse callback doesn't always expose trace_id directly
        # We'll construct the URL based on session/user if possible
        if hasattr(self._callback, 'trace_id') and self._callback.trace_id:
            trace_id = self._callback.trace_id
            return f"{self.base_url}/trace/{trace_id}"

        # Fallback: return traces page
        return f"{self.base_url}/traces"

    def flush(self):
        """
        Flush pending traces to LangFuse.

        Call this after workflow completes to ensure all data is uploaded.

        Example:
            >>> tracker = LangFuseTracker()
            >>> callback = tracker.get_callback()
            >>>
            >>> # ... workflow executes ...
            >>>
            >>> tracker.flush()  # Ensure all traces uploaded
        """
        if self._callback:
            self._callback.flush()

    def get_stats(self) -> dict:
        """
        Get tracking statistics.

        Returns:
            Dict with configuration and status

        Example:
            >>> tracker = LangFuseTracker()
            >>> stats = tracker.get_stats()
            >>> print(f"LangFuse URL: {stats['base_url']}")
            >>> print(f"Active: {stats['active']}")
        """
        return {
            "base_url": self.base_url,
            "active": self._callback is not None,
            "configured": bool(self.secret_key and self.public_key)
        }


def create_tracked_callback(
    session_id: Optional[str] = None,
    user_id: Optional[str] = None
) -> tuple[CallbackHandler, LangFuseTracker]:
    """
    Convenience function to create tracker and callback in one call.

    Args:
        session_id: Optional session identifier
        user_id: Optional user identifier

    Returns:
        Tuple of (callback_handler, tracker)

    Example:
        >>> callback, tracker = create_tracked_callback(
        ...     session_id="sess_123",
        ...     user_id="user_456"
        ... )
        >>>
        >>> agent = factory.create_agent(..., callbacks=[callback])
        >>>
        >>> # ... workflow executes ...
        >>>
        >>> print(f"View trace: {tracker.get_trace_link()}")
    """
    tracker = LangFuseTracker()
    callback = tracker.get_callback(session_id=session_id, user_id=user_id)
    return callback, tracker

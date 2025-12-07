"""
errors.py - Error categorization and tracking

Phase 5 Enhancement: Categorize and track errors for better debugging
and alerting in production environments.

Features:
- Error categorization (auth, rate_limit, network, validation, etc.)
- Error frequency tracking
- Error details capture (stack traces, context)
- Alert threshold detection
- Error pattern analysis
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from collections import defaultdict, Counter
import traceback


class ErrorCategory(str, Enum):
    """Error categories for classification."""
    # API/Provider Errors
    AUTHENTICATION = "authentication"  # API key invalid
    AUTHORIZATION = "authorization"   # Permission denied
    RATE_LIMIT = "rate_limit"          # Rate limit exceeded
    QUOTA_EXCEEDED = "quota_exceeded"  # Usage quota exceeded

    # Network Errors
    NETWORK = "network"                # Connection failed
    TIMEOUT = "timeout"                # Request timeout
    SERVICE_UNAVAILABLE = "service_unavailable"  # Provider down

    # Request Errors
    VALIDATION = "validation"          # Invalid input
    NOT_FOUND = "not_found"            # Resource not found
    CONFLICT = "conflict"              # Resource conflict

    # Processing Errors
    INTERNAL = "internal"              # Internal error
    UNKNOWN = "unknown"                # Unclassified error

    # Application Errors
    TOOL_ERROR = "tool_error"          # Tool execution failed
    AGENT_ERROR = "agent_error"        # Agent logic error
    MEMORY_ERROR = "memory_error"      # Memory/storage error


@dataclass
class ErrorEvent:
    """
    Represents a single error occurrence.

    Captures full error context for debugging and analysis.
    """
    category: ErrorCategory
    message: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    trace_id: Optional[str] = None
    user_id: Optional[str] = None
    agent_name: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    stack_trace: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert error event to dictionary."""
        return {
            "category": self.category.value,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "trace_id": self.trace_id,
            "user_id": self.user_id,
            "agent_name": self.agent_name,
            "provider": self.provider,
            "model": self.model,
            "stack_trace": self.stack_trace,
            "metadata": self.metadata
        }


class ErrorTracker:
    """
    Tracks and categorizes errors for production monitoring.

    Features:
    - Automatic error categorization
    - Frequency tracking per category
    - Alert threshold detection
    - Error pattern analysis

    Usage:
        tracker = ErrorTracker(alert_threshold=10)

        try:
            result = api_call()
        except Exception as e:
            tracker.record_error(
                exception=e,
                category=ErrorCategory.RATE_LIMIT,
                trace_id="abc123",
                agent_name="research"
            )

        if tracker.should_alert(ErrorCategory.RATE_LIMIT):
            send_alert("Rate limit errors spiking")

        summary = tracker.summary()
    """

    def __init__(
        self,
        alert_threshold: int = 10,
        window_minutes: int = 60,
        max_events: int = 1000
    ):
        """
        Initialize error tracker.

        Args:
            alert_threshold: Number of errors to trigger alert
            window_minutes: Time window for threshold (not implemented yet)
            max_events: Maximum events to store (LRU eviction)
        """
        self.alert_threshold = alert_threshold
        self.window_minutes = window_minutes
        self.max_events = max_events

        # Storage
        self.events: List[ErrorEvent] = []
        self.category_counts: Counter = Counter()
        self.agent_errors: Dict[str, Counter] = defaultdict(Counter)
        self.provider_errors: Dict[str, Counter] = defaultdict(Counter)

    def record_error(
        self,
        exception: Optional[Exception] = None,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        message: Optional[str] = None,
        trace_id: Optional[str] = None,
        user_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        **metadata: Any
    ) -> ErrorEvent:
        """
        Record an error event.

        Args:
            exception: Exception object (optional)
            category: Error category
            message: Error message (uses exception message if not provided)
            trace_id: Request trace ID
            user_id: User identifier
            agent_name: Agent that errored
            provider: LLM provider
            model: LLM model
            **metadata: Additional error metadata

        Returns:
            Created ErrorEvent
        """
        # Extract message from exception if not provided
        if message is None and exception is not None:
            message = str(exception)
        elif message is None:
            message = "Unknown error"

        # Get stack trace if exception provided
        stack_trace = None
        if exception is not None:
            stack_trace = "".join(traceback.format_exception(
                type(exception), exception, exception.__traceback__
            ))

        # Categorize exception if category is UNKNOWN
        if category == ErrorCategory.UNKNOWN and exception is not None:
            category = self._categorize_exception(exception)

        # Create error event
        event = ErrorEvent(
            category=category,
            message=message,
            trace_id=trace_id,
            user_id=user_id,
            agent_name=agent_name,
            provider=provider,
            model=model,
            stack_trace=stack_trace,
            metadata=metadata
        )

        # Store event (LRU eviction)
        self.events.append(event)
        if len(self.events) > self.max_events:
            self.events.pop(0)

        # Update counters
        self.category_counts[category] += 1

        if agent_name:
            self.agent_errors[agent_name][category] += 1

        if provider:
            self.provider_errors[provider][category] += 1

        return event

    def _categorize_exception(self, exception: Exception) -> ErrorCategory:
        """
        Automatically categorize exception based on type and message.

        Args:
            exception: Exception to categorize

        Returns:
            ErrorCategory
        """
        error_msg = str(exception).lower()
        error_type = type(exception).__name__.lower()

        # Authentication errors
        if any(keyword in error_msg for keyword in ["api key", "authentication", "unauthorized", "invalid key"]):
            return ErrorCategory.AUTHENTICATION

        if any(keyword in error_msg for keyword in ["authorization", "forbidden", "permission denied"]):
            return ErrorCategory.AUTHORIZATION

        # Rate limiting
        if any(keyword in error_msg for keyword in ["rate limit", "too many requests", "429"]):
            return ErrorCategory.RATE_LIMIT

        if any(keyword in error_msg for keyword in ["quota", "limit exceeded"]):
            return ErrorCategory.QUOTA_EXCEEDED

        # Network errors
        if any(keyword in error_type for keyword in ["connection", "network", "socket"]):
            return ErrorCategory.NETWORK

        if any(keyword in error_msg for keyword in ["timeout", "timed out"]):
            return ErrorCategory.TIMEOUT

        if any(keyword in error_msg for keyword in ["503", "service unavailable", "server error"]):
            return ErrorCategory.SERVICE_UNAVAILABLE

        # Request errors
        if any(keyword in error_type for keyword in ["validation", "value"]):
            return ErrorCategory.VALIDATION

        if any(keyword in error_msg for keyword in ["not found", "404"]):
            return ErrorCategory.NOT_FOUND

        # Default
        return ErrorCategory.UNKNOWN

    def should_alert(self, category: Optional[ErrorCategory] = None) -> bool:
        """
        Check if error count exceeds alert threshold.

        Args:
            category: Specific category to check (or all if None)

        Returns:
            True if threshold exceeded
        """
        if category:
            return self.category_counts[category] >= self.alert_threshold
        else:
            return sum(self.category_counts.values()) >= self.alert_threshold

    def get_errors_by_category(self, category: ErrorCategory) -> List[ErrorEvent]:
        """
        Get all errors for a specific category.

        Args:
            category: Error category

        Returns:
            List of error events
        """
        return [e for e in self.events if e.category == category]

    def get_recent_errors(self, limit: int = 10) -> List[ErrorEvent]:
        """
        Get most recent errors.

        Args:
            limit: Maximum number of errors to return

        Returns:
            List of recent error events
        """
        return self.events[-limit:]

    def clear(self) -> None:
        """Clear all error events and counters."""
        self.events.clear()
        self.category_counts.clear()
        self.agent_errors.clear()
        self.provider_errors.clear()

    def summary(self) -> Dict[str, Any]:
        """
        Get error tracking summary.

        Returns:
            Dictionary with error statistics
        """
        total_errors = len(self.events)

        # Top error categories
        top_categories = [
            {"category": cat.value, "count": count}
            for cat, count in self.category_counts.most_common(5)
        ]

        # Agents with most errors
        top_agents = []
        for agent, counts in self.agent_errors.items():
            total = sum(counts.values())
            top_agents.append({"agent": agent, "errors": total})
        top_agents.sort(key=lambda x: x["errors"], reverse=True)
        top_agents = top_agents[:5]

        # Providers with most errors
        top_providers = []
        for provider, counts in self.provider_errors.items():
            total = sum(counts.values())
            top_providers.append({"provider": provider, "errors": total})
        top_providers.sort(key=lambda x: x["errors"], reverse=True)
        top_providers = top_providers[:5]

        return {
            "total_errors": total_errors,
            "unique_categories": len(self.category_counts),
            "top_categories": top_categories,
            "top_agents": top_agents,
            "top_providers": top_providers,
            "alert_status": {
                "threshold": self.alert_threshold,
                "should_alert": self.should_alert(),
                "categories_alerting": [
                    cat.value for cat, count in self.category_counts.items()
                    if count >= self.alert_threshold
                ]
            }
        }


# Global error tracker instance
_global_tracker: Optional[ErrorTracker] = None


def get_error_tracker(alert_threshold: int = 10) -> ErrorTracker:
    """
    Get or create global error tracker.

    Args:
        alert_threshold: Alert threshold for new tracker

    Returns:
        ErrorTracker instance
    """
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = ErrorTracker(alert_threshold=alert_threshold)
    return _global_tracker

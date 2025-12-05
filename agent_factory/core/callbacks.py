"""
Callbacks - Event System for Agent Observability

Generated from: specs/callbacks-v1.0.md
Generated on: 2025-12-05
Spec SHA256: 21271162b84a

REGENERATION: python factory.py specs/callbacks-v1.0.md

Provides pub/sub event system for real-time monitoring, logging, and audit trails
of agent operations. Zero-overhead design with 1000-event history buffer.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Any, Optional, Callable


# ═══════════════════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════════════════


class EventType(str, Enum):
    """
    Standard event types for agent observability.

    Implements: REQ-CB-001 (Event Types)
    Spec: specs/callbacks-v1.0.md#section-2.1
    """
    AGENT_START = "agent_start"      # Agent begins processing query
    AGENT_END = "agent_end"          # Agent completes successfully
    ROUTE_DECISION = "route_decision"  # Orchestrator selects agent
    ERROR = "error"                  # Any error condition
    TOOL_CALL = "tool_call"          # Agent invokes a tool


# ═══════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class Event:
    """
    Single event in the system.

    Implements: REQ-CB-002 (Event Structure)
    Spec: specs/callbacks-v1.0.md#section-2.2
    """
    event_type: EventType            # Type of event
    timestamp: datetime              # When event occurred (UTC)
    data: Dict[str, Any]            # Event-specific payload
    agent_name: Optional[str] = None  # Which agent emitted this

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert event to JSON-serializable dictionary.

        Implements: REQ-CB-002

        Returns:
            Dictionary with all event fields
        """
        return {
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "agent_name": self.agent_name
        }


# ═══════════════════════════════════════════════════════════════════════════
# EVENT BUS - PUB/SUB SYSTEM
# ═══════════════════════════════════════════════════════════════════════════


class EventBus:
    """
    Publisher/subscriber event system with history tracking.

    Implements: REQ-CB-003 through REQ-CB-008
    Spec: specs/callbacks-v1.0.md

    Features:
    - Multiple listeners per event type
    - Listener error isolation (one failure doesn't crash bus)
    - Circular buffer history (configurable max size)
    - Event filtering and querying

    Attributes:
        _listeners: Registered callbacks by event type
        _history: Chronological list of events
        _max_history: Maximum events to store
    """

    def __init__(self, max_history: int = 1000):
        """
        Initialize event bus with configurable history.

        Implements: REQ-CB-003

        Args:
            max_history: Maximum events to store (default 1000)

        Troubleshooting:
            - If memory grows → Reduce max_history
            - If events missing → Increase max_history
            - If listeners not firing → Check registration before emit
        """
        self._listeners: Dict[EventType, List[Callable[[Event], None]]] = {}
        self._history: List[Event] = []
        self._max_history = max_history

    def on(self, event_type: EventType, callback: Callable[[Event], None]) -> None:
        """
        Register listener for specific event type.

        Implements: REQ-CB-005 (Listener Management)
        Spec: specs/callbacks-v1.0.md#section-2.5

        Args:
            event_type: Type of event to listen for
            callback: Function to call when event emitted

        Examples:
            >>> bus = EventBus()
            >>> bus.on(EventType.AGENT_START, lambda e: print(e.data))
        """
        if event_type not in self._listeners:
            self._listeners[event_type] = []

        self._listeners[event_type].append(callback)

    def off(self, event_type: EventType, callback: Callable[[Event], None]) -> None:
        """
        Unregister listener for specific event type.

        Implements: REQ-CB-005

        Args:
            event_type: Type of event to stop listening for
            callback: Function to remove
        """
        if event_type in self._listeners:
            try:
                self._listeners[event_type].remove(callback)
            except ValueError:
                pass  # Callback not registered, ignore

    def emit(
        self,
        event_type: EventType,
        data: Dict[str, Any],
        agent_name: Optional[str] = None
    ) -> Event:
        """
        Emit event to all registered listeners.

        Implements: REQ-CB-006 (emit() Behavior)
        Spec: specs/callbacks-v1.0.md#section-4.1

        Process:
        1. Create Event object with current UTC timestamp
        2. Add to history (circular buffer)
        3. Call all registered listeners
        4. Isolate listener errors (continue on exception)

        Args:
            event_type: Type of event
            data: Event-specific data
            agent_name: Optional agent identifier

        Returns:
            The created Event object

        Troubleshooting:
            - If listeners not called → Check they're registered first
            - If listener crashes bus → Should never happen (file bug)
            - If events lost → Increase max_history size
        """
        # Create event with UTC timestamp
        event = Event(
            event_type=event_type,
            timestamp=datetime.utcnow(),
            data=data,
            agent_name=agent_name
        )

        # Add to history (circular buffer behavior)
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history.pop(0)  # Remove oldest

        # Call all listeners for this event type
        listeners = self._listeners.get(event_type, [])
        for callback in listeners:
            try:
                callback(event)
            except Exception as e:
                # Listener error isolation - log but don't crash
                print(f"[EventBus] Callback error: {e}")

        return event

    def get_history(
        self,
        event_type: Optional[EventType] = None,
        agent_name: Optional[str] = None,
        limit: int = 100
    ) -> List[Event]:
        """
        Query event history with optional filters.

        Implements: REQ-CB-004 (Event History)
        Spec: specs/callbacks-v1.0.md#section-2.4

        Args:
            event_type: Filter by event type (None = all types)
            agent_name: Filter by agent name (None = all agents)
            limit: Maximum events to return (most recent)

        Returns:
            List of matching events (newest first)

        Examples:
            >>> # Get last 10 errors
            >>> errors = bus.get_history(EventType.ERROR, limit=10)
            >>> # Get all events from specific agent
            >>> agent_events = bus.get_history(agent_name="research")
        """
        # Start with full history
        filtered = self._history

        # Apply filters
        if event_type is not None:
            filtered = [e for e in filtered if e.event_type == event_type]

        if agent_name is not None:
            filtered = [e for e in filtered if e.agent_name == agent_name]

        # Return most recent N events
        return filtered[-limit:]

    def clear_history(self) -> None:
        """
        Clear all stored events from history.

        Implements: REQ-CB-004

        Use case: Reset state between test runs or sessions
        """
        self._history = []


# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════


def create_default_event_bus(verbose: bool = False) -> EventBus:
    """
    Create EventBus with optional console logging.

    Implements: REQ-CB-009 (create_default_event_bus)
    Spec: specs/callbacks-v1.0.md#section-5.1

    If verbose=True, automatically logs all events to console in format:
    [event_type] agent_name: {data}

    Args:
        verbose: Enable console logging for all events

    Returns:
        Configured EventBus instance

    Examples:
        >>> # Development mode with logging
        >>> bus = create_default_event_bus(verbose=True)
        >>> bus.emit(EventType.AGENT_START, {"query": "test"}, agent_name="research")
        [agent_start] research: {'query': 'test'}
    """
    bus = EventBus()

    if verbose:
        def log_event(event: Event):
            agent = event.agent_name or "system"
            print(f"[{event.event_type.value}] {agent}: {event.data}")

        # Register logger for all event types
        for event_type in EventType:
            bus.on(event_type, log_event)

    return bus

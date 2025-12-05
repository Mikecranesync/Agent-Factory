"""
Event system for agent observability.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from enum import Enum


class EventType(str, Enum):
    """Standard event types."""
    AGENT_START = "agent_start"
    AGENT_END = "agent_end"
    ROUTE_DECISION = "route_decision"
    ERROR = "error"
    TOOL_CALL = "tool_call"


@dataclass
class Event:
    """Single event record."""
    event_type: EventType
    timestamp: datetime
    data: Dict[str, Any]
    agent_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "agent_name": self.agent_name,
            "data": self.data
        }


class EventBus:
    """
    Pub/sub event system for agent observability.

    Usage:
        bus = EventBus()
        bus.on(EventType.AGENT_START, lambda e: print(f"Started: {e.agent_name}"))
        bus.emit(EventType.AGENT_START, {"query": "hello"}, agent_name="greeter")
    """

    def __init__(self):
        self._listeners: Dict[EventType, List[Callable[[Event], None]]] = {}
        self._history: List[Event] = []
        self._max_history: int = 1000

    def on(self, event_type: EventType, callback: Callable[[Event], None]) -> None:
        """Register a callback for an event type."""
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(callback)

    def off(self, event_type: EventType, callback: Callable[[Event], None]) -> None:
        """Remove a callback."""
        if event_type in self._listeners:
            self._listeners[event_type] = [
                cb for cb in self._listeners[event_type] if cb != callback
            ]

    def emit(
        self,
        event_type: EventType,
        data: Dict[str, Any],
        agent_name: Optional[str] = None
    ) -> Event:
        """Emit an event to all registered listeners."""
        event = Event(
            event_type=event_type,
            timestamp=datetime.now(),
            data=data,
            agent_name=agent_name
        )

        # Store in history
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

        # Notify listeners
        for callback in self._listeners.get(event_type, []):
            try:
                callback(event)
            except Exception as e:
                # Don't let callback errors break the system
                print(f"[EventBus] Callback error: {e}")

        return event

    def get_history(
        self,
        event_type: Optional[EventType] = None,
        agent_name: Optional[str] = None,
        limit: int = 100
    ) -> List[Event]:
        """Query event history with optional filters."""
        results = self._history

        if event_type:
            results = [e for e in results if e.event_type == event_type]

        if agent_name:
            results = [e for e in results if e.agent_name == agent_name]

        return results[-limit:]

    def clear_history(self) -> None:
        """Clear event history."""
        self._history = []


# Convenience function for creating pre-configured event bus
def create_default_event_bus(verbose: bool = False) -> EventBus:
    """Create EventBus with standard logging if verbose."""
    bus = EventBus()

    if verbose:
        def log_event(event: Event):
            print(f"[{event.event_type.value}] {event.agent_name or 'system'}: {event.data}")

        for event_type in EventType:
            bus.on(event_type, log_event)

    return bus

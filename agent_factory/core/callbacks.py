"""
Callbacks - Event System for Agent Observability

PURPOSE:
    Provides pub/sub (publisher/subscriber) event system for monitoring agent operations.
    Like a PLC data logging system that records all machine events to HMI/SCADA.

Generated from: specs/callbacks-v1.0.md
Generated on: 2025-12-05
Spec SHA256: 21271162b84a

REGENERATION: python factory.py specs/callbacks-v1.0.md

WHAT THIS DOES:
    1. Defines standard event types (agent start, end, errors, routing, tool calls)
    2. Provides EventBus for pub/sub communication (decouple producers/consumers)
    3. Maintains circular buffer history (configurable max size, default 1000 events)
    4. Isolates listener errors (one bad listener doesn't crash system)
    5. Enables real-time monitoring, logging, audit trails

WHY WE NEED THIS:
    - Observability: Track what agents are doing in real-time
    - Debugging: Replay event history to diagnose issues
    - Monitoring: Alert on errors or performance issues
    - Audit: Compliance trails for who did what when
    - Decoupling: Producers don't need to know about consumers

PLC ANALOGY:
    Like a PLC data logging and event notification system:
    - Event types = PLC alarm/status categories (fault, warning, info)
    - EventBus = Data logging buffer that records all machine events
    - Listeners = HMI screens and SCADA systems subscribed to events
    - History = Circular buffer like PLC event log (keeps last N events)
    - Isolated errors = If HMI crashes, PLC keeps running
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

    PURPOSE:
        Defines the fixed set of event types the system can emit.
        Like PLC alarm/status categories - standardized event classification.

    WHAT THIS DEFINES:
        - AGENT_START: Agent begins processing a query
        - AGENT_END: Agent completes successfully (with output)
        - ROUTE_DECISION: Orchestrator selects which agent to use
        - ERROR: Any error condition (agent failure, routing failure, etc.)
        - TOOL_CALL: Agent invokes a tool (search, file access, API call)

    WHY WE NEED THIS:
        - Standardization: Everyone uses same event type names
        - Type safety: Can't emit invalid event types (enum constraint)
        - Filtering: Easy to query history by type
        - Monitoring: Subscribe to specific event types

    PLC ANALOGY:
        Like PLC event categories:
        - AGENT_START = Station cycle start
        - AGENT_END = Station cycle complete
        - ROUTE_DECISION = Master routing decision
        - ERROR = Fault alarm
        - TOOL_CALL = Function block call

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

    PURPOSE:
        Represents one logged event with type, timestamp, data, and source agent.
        Like a PLC event log entry - who, what, when, details.

    WHAT THIS STORES:
        - event_type: Category of event (EventType enum)
        - timestamp: When event occurred (datetime, UTC)
        - data: Event-specific details (dict)
        - agent_name: Which agent emitted this (optional)

    WHY WE NEED THIS:
        - Structured logging: Consistent format for all events
        - Serializable: Can convert to JSON for storage/transmission
        - Traceable: Know which agent did what and when
        - Queryable: Filter history by type, agent, time range

    PLC ANALOGY:
        Like a PLC event log record:
        - event_type = Alarm category (fault, warning, info)
        - timestamp = Event occurrence time
        - data = Alarm details (station, value, message)
        - agent_name = Station ID that triggered alarm

    Implements: REQ-CB-002 (Event Structure)
    Spec: specs/callbacks-v1.0.md#section-2.2
    """
    event_type: EventType            # Type of event (AGENT_START, ERROR, etc.)
    timestamp: datetime              # When event occurred (UTC)
    data: Dict[str, Any]            # Event-specific payload (query, output, error, etc.)
    agent_name: Optional[str] = None  # Which agent emitted this (None = system event)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert event to JSON-serializable dictionary.

        PURPOSE:
            Serializes event for storage, transmission, or API responses.
            Like exporting PLC event log to CSV for external analysis.

        WHAT THIS DOES:
            1. Converts event_type enum to string value
            2. Converts timestamp to ISO 8601 string
            3. Copies data dict as-is (must already be JSON-safe)
            4. Returns dictionary ready for json.dumps()

        WHY WE NEED THIS:
            - API responses: Return events as JSON
            - Storage: Save events to database or file
            - Interoperability: Other systems can parse events

        OUTPUTS:
            Dictionary with keys: event_type, timestamp, data, agent_name

        PLC ANALOGY:
            Like exporting PLC event log entry to CSV row:
            - Enum becomes text
            - Timestamp becomes ISO string
            - Data remains structured

        Implements: REQ-CB-002
        """
        return {
            "event_type": self.event_type.value,  # Enum to string
            "timestamp": self.timestamp.isoformat(),  # Datetime to ISO string
            "data": self.data,  # Already dict
            "agent_name": self.agent_name  # String or None
        }


# ═══════════════════════════════════════════════════════════════════════════
# EVENT BUS - PUB/SUB SYSTEM
# ═══════════════════════════════════════════════════════════════════════════


class EventBus:
    """
    Publisher/subscriber event system with history tracking.

    PURPOSE:
        Central event hub for agent observability - producers emit events, consumers listen.
        Like a PLC data logging system that records all events and notifies subscribed HMIs.

    WHAT THIS DOES:
        1. Maintains registry of listeners (callbacks) per event type
        2. Emits events to all registered listeners for that type
        3. Stores event history in circular buffer (configurable size)
        4. Isolates listener errors (one bad listener doesn't crash bus)
        5. Provides history querying (filter by type, agent, limit)

    WHY WE NEED THIS:
        - Decoupling: Producers don't know about consumers (loose coupling)
        - Observability: Track all agent operations in one place
        - Debugging: Replay event history to diagnose issues
        - Monitoring: Multiple listeners can monitor same events
        - Reliability: Listener failures don't affect producers

    ARCHITECTURE:
        Producers (orchestrator, agents) → emit() → EventBus → notify listeners
                                                            ↓
                                                      Circular buffer history

    PLC ANALOGY:
        Like a PLC data logging and alarm distribution system:
        - Producers = PLC stations emitting alarms/status
        - EventBus = Central alarm/data logger
        - Listeners = HMI screens subscribed to specific alarm types
        - History = Circular event log buffer (keeps last N events)
        - Error isolation = If one HMI crashes, others still get events

    Implements: REQ-CB-003 through REQ-CB-008
    Spec: specs/callbacks-v1.0.md

    Attributes:
        _listeners: Registered callbacks by event type
        _history: Chronological list of events
        _max_history: Maximum events to store
    """

    def __init__(self, max_history: int = 1000):
        """
        Initialize event bus with configurable history.

        PURPOSE:
            Sets up empty event bus ready to register listeners and emit events.
            Like initializing a PLC data logger before connecting sensors/HMIs.

        WHAT THIS DOES:
            1. Creates empty listener registry (dict of lists)
            2. Creates empty event history (list)
            3. Sets maximum history size (circular buffer limit)

        WHY WE NEED THIS:
            - Configurable buffer: Adjust memory vs history depth trade-off
            - Clean start: No pre-existing listeners or events

        INPUTS:
            max_history: Maximum events to store before oldest are dropped (default 1000)

        PLC ANALOGY:
            Like initializing PLC event log:
            - max_history = Log buffer size (e.g., 1000 events)
            - Oldest events auto-deleted when buffer full (FIFO)

        EDGE CASES:
            - max_history=0 → No history stored (events still emitted to listeners)
            - max_history=999999 → High memory usage, may cause issues

        TROUBLESHOOTING:
            - Memory growing unbounded → Reduce max_history
            - Events missing from history → Increase max_history
            - Listeners not firing → Check registration happens before emit

        Implements: REQ-CB-003
        """
        # STEP 1: Initialize empty listener registry (dict of event_type -> list of callbacks)
        self._listeners: Dict[EventType, List[Callable[[Event], None]]] = {}

        # STEP 2: Initialize empty event history (chronological list)
        self._history: List[Event] = []

        # STEP 3: Store maximum history size for circular buffer behavior
        self._max_history = max_history

    def on(self, event_type: EventType, callback: Callable[[Event], None]) -> None:
        """
        Register listener for specific event type (subscribe).

        PURPOSE:
            Adds a callback function that will be called when events of specified type are emitted.
            Like connecting an HMI screen to receive specific PLC alarm types.

        WHAT THIS DOES:
            1. Creates listener list for this event type if it doesn't exist
            2. Appends callback to list of listeners for this type
            3. Callback will be called for all future events of this type

        WHY WE NEED THIS:
            - Selective monitoring: Only listen for events you care about
            - Multiple listeners: Many callbacks can listen to same event type
            - Dynamic: Add listeners at runtime

        INPUTS:
            event_type: Type of event to listen for (e.g., EventType.ERROR)
            callback: Function with signature `def func(event: Event) -> None`

        PLC ANALOGY:
            Like subscribing HMI to specific PLC alarm types:
            - event_type = Alarm category (faults, warnings, info)
            - callback = HMI update function when alarm fires
            - Multiple HMIs can subscribe to same alarm type

        EDGE CASES:
            - Same callback registered twice → Both will be called (duplicates allowed)
            - Callback raises exception → Isolated in emit(), doesn't crash bus

        Examples:
            >>> bus = EventBus()
            >>> bus.on(EventType.AGENT_START, lambda e: print(f"Agent started: {e.agent_name}"))
            >>> bus.on(EventType.ERROR, lambda e: logging.error(e.data))

        Implements: REQ-CB-005 (Listener Management)
        Spec: specs/callbacks-v1.0.md#section-2.5
        """
        # STEP 1: Create listener list for this event type if doesn't exist
        if event_type not in self._listeners:
            self._listeners[event_type] = []

        # STEP 2: Append callback to listener list
        self._listeners[event_type].append(callback)

    def off(self, event_type: EventType, callback: Callable[[Event], None]) -> None:
        """
        Unregister listener for specific event type (unsubscribe).

        PURPOSE:
            Removes a previously registered callback so it no longer receives events.
            Like disconnecting an HMI from receiving specific PLC alarm types.

        WHAT THIS DOES:
            1. Finds listener list for this event type
            2. Removes callback from list (if present)
            3. Silently ignores if callback wasn't registered (no error)

        WHY WE NEED THIS:
            - Cleanup: Remove listeners when no longer needed
            - Dynamic: Change subscriptions at runtime
            - Memory: Prevent listener leak

        INPUTS:
            event_type: Type of event to stop listening for
            callback: Exact callback function to remove (must be same object)

        PLC ANALOGY:
            Like disconnecting HMI from PLC alarm subscription:
            - Stops receiving those alarm updates
            - Other HMIs still receive alarms (doesn't affect them)

        EDGE CASES:
            - Callback not registered → Silently ignored (no error)
            - Multiple instances of callback → Removes first one only
            - event_type has no listeners → Silently ignored

        Implements: REQ-CB-005
        """
        # STEP 1: Check if event type has any listeners
        if event_type in self._listeners:
            try:
                # STEP 2: Remove callback from listener list
                self._listeners[event_type].remove(callback)
            except ValueError:
                # STEP 3: Callback not in list - silently ignore
                pass  # Not an error, just wasn't registered

    def emit(
        self,
        event_type: EventType,
        data: Dict[str, Any],
        agent_name: Optional[str] = None
    ) -> Event:
        """
        Emit event to all registered listeners (publish).

        PURPOSE:
            Creates and broadcasts an event to all registered listeners for that type.
            Like a PLC triggering an alarm that notifies all subscribed HMI screens.

        WHAT THIS DOES:
            1. Creates Event object with current UTC timestamp
            2. Adds event to circular buffer history
            3. Notifies all registered listeners for this event type
            4. Isolates listener errors (one failure doesn't crash bus)
            5. Returns created Event object

        WHY WE NEED THIS:
            - Broadcast: One emit reaches multiple listeners
            - Decoupled: Producer doesn't know who's listening
            - Reliable: Listener failures don't affect producer
            - Traceable: All events logged to history

        INPUTS:
            event_type: Type of event (e.g., EventType.AGENT_START)
            data: Event-specific payload (e.g., {"query": "...", "duration_ms": 123})
            agent_name: Optional agent identifier (e.g., "calendar_agent")

        OUTPUTS:
            Created Event object (with timestamp filled in)

        PROCESS:
            1. Create Event with UTC timestamp
            2. Append to history, drop oldest if buffer full (circular buffer)
            3. Get all listeners for this event type
            4. Call each listener with event
            5. If listener throws exception, log error and continue to next
            6. Return event

        EDGE CASES:
            - No listeners registered → Event still logged to history
            - Listener throws exception → Logged, other listeners still called
            - max_history=0 → Event not stored but still emitted
            - History full → Oldest event dropped (FIFO)

        TROUBLESHOOTING:
            - Listeners not called → Check they're registered before emit
            - Listener crashes entire bus → File bug (should be isolated)
            - Events missing from history → Buffer too small, increase max_history
            - Listener errors logged → Check listener implementation

        PLC ANALOGY:
            Like PLC alarm broadcast:
            - Event = Alarm condition occurred
            - History = Event log buffer (FIFO, keeps last N)
            - Listeners = HMI screens subscribed to this alarm type
            - Error isolation = If one HMI crashes, others still get alarm
            - Returns event = Confirmation alarm was logged

        Implements: REQ-CB-006 (emit() Behavior)
        Spec: specs/callbacks-v1.0.md#section-4.1
        """
        # STEP 1: Create event object with current UTC timestamp
        event = Event(
            event_type=event_type,
            timestamp=datetime.utcnow(),  # UTC for consistency across timezones
            data=data,
            agent_name=agent_name
        )

        # STEP 2: Add to history with circular buffer behavior
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history.pop(0)  # Remove oldest event (FIFO)

        # STEP 3: Get all registered listeners for this event type
        listeners = self._listeners.get(event_type, [])

        # STEP 4: Call each listener with error isolation
        for callback in listeners:
            try:
                callback(event)  # Notify listener
            except Exception as e:
                # STEP 5: Isolate listener errors (don't crash bus)
                print(f"[EventBus] Callback error: {e}")
                # Continue to next listener (one failure doesn't affect others)

        # STEP 6: Return created event
        return event

    def get_history(
        self,
        event_type: Optional[EventType] = None,
        agent_name: Optional[str] = None,
        limit: int = 100
    ) -> List[Event]:
        """
        Query event history with optional filters.

        PURPOSE:
            Retrieves historical events for debugging, monitoring, or audit trails.
            Like querying a PLC event log to diagnose machine faults.

        WHAT THIS DOES:
            1. Starts with full event history
            2. Filters by event_type if specified
            3. Filters by agent_name if specified
            4. Returns most recent N events (tail of list)

        WHY WE NEED THIS:
            - Debugging: Replay sequence of events to diagnose issues
            - Monitoring: Check recent errors or agent activity
            - Audit: Compliance trail of who did what when
            - Analytics: Analyze agent usage patterns

        INPUTS:
            event_type: Filter by event type (None = all types)
            agent_name: Filter by agent name (None = all agents)
            limit: Maximum events to return (most recent, default 100)

        OUTPUTS:
            List of Event objects matching filters (newest last)

        EDGE CASES:
            - Empty history → Returns empty list
            - Filters match nothing → Returns empty list
            - limit > available events → Returns all matching events
            - limit=0 → Returns empty list

        TROUBLESHOOTING:
            - No events returned → Check history not empty, filters not too strict
            - Too many events → Reduce limit parameter
            - Missing events → Check max_history buffer size

        PLC ANALOGY:
            Like querying PLC event log:
            - event_type filter = Show only fault alarms
            - agent_name filter = Show only events from Station 3
            - limit = Show last 100 events
            - Returns chronological list

        Examples:
            >>> # Get last 10 errors
            >>> errors = bus.get_history(EventType.ERROR, limit=10)
            >>> # Get all events from specific agent
            >>> agent_events = bus.get_history(agent_name="research")
            >>> # Get last 50 routing decisions
            >>> routes = bus.get_history(EventType.ROUTE_DECISION, limit=50)

        Implements: REQ-CB-004 (Event History)
        Spec: specs/callbacks-v1.0.md#section-2.4
        """
        # STEP 1: Start with full history
        filtered = self._history

        # STEP 2: Apply event_type filter if specified
        if event_type is not None:
            filtered = [e for e in filtered if e.event_type == event_type]

        # STEP 3: Apply agent_name filter if specified
        if agent_name is not None:
            filtered = [e for e in filtered if e.agent_name == agent_name]

        # STEP 4: Return most recent N events (tail of list)
        return filtered[-limit:]  # Negative index takes from end

    def clear_history(self) -> None:
        """
        Clear all stored events from history.

        PURPOSE:
            Resets event history to empty state (listeners remain registered).
            Like clearing a PLC event log while keeping alarm subscriptions active.

        WHAT THIS DOES:
            1. Replaces history list with empty list
            2. Listeners remain registered (doesn't affect subscriptions)
            3. Future events will be logged normally

        WHY WE NEED THIS:
            - Testing: Reset state between test runs
            - Memory: Clear old events when no longer needed
            - Sessions: Start fresh log for new session

        PLC ANALOGY:
            Like clearing PLC event log:
            - Event history deleted
            - Alarm subscriptions unchanged (HMIs still connected)
            - New alarms will be logged normally

        EDGE CASES:
            - Already empty → No change (idempotent)
            - Events in progress → Cleared immediately (may lose recent events)

        TROUBLESHOOTING:
            - Events reappear → New events being emitted (working as designed)
            - Listeners stopped → Check listener registration (shouldn't be affected)

        Use cases:
            - Reset state between test runs
            - Clear debug logs
            - Start fresh session

        Implements: REQ-CB-004
        """
        # STEP 1: Replace history with empty list (GC will clean up old events)
        self._history = []


# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════


def create_default_event_bus(verbose: bool = False) -> EventBus:
    """
    Create EventBus with optional console logging.

    PURPOSE:
        Convenience function to create pre-configured EventBus for common use cases.
        Like initializing a PLC data logger with default HMI console attached.

    WHAT THIS DOES:
        1. Creates new EventBus instance with default settings (1000 event history)
        2. If verbose=True, registers console logger for all event types
        3. Returns configured EventBus ready to use

    WHY WE NEED THIS:
        - Convenience: One-liner to get working event bus
        - Development: Easy to enable verbose logging during debugging
        - Default settings: Reasonable defaults for most use cases

    INPUTS:
        verbose: Enable console logging for all events (default False)

    OUTPUTS:
        Configured EventBus instance ready to use

    VERBOSE MODE:
        When enabled, prints all events to console in format:
        [event_type] agent_name: {data}

        Example output:
        [agent_start] research: {'query': 'What is Python?'}
        [route_decision] system: {'matched_agent': 'research', 'method': 'keyword'}
        [agent_end] research: {'output': '...', 'duration_ms': 1234}

    PLC ANALOGY:
        Like initializing PLC logger with options:
        - verbose=False: Log to file only (no console output)
        - verbose=True: Log to file AND console (debugging mode)

    EDGE CASES:
        - verbose=False → No console output (quiet mode)
        - verbose=True → All events printed to console (may be noisy)

    TROUBLESHOOTING:
        - Too much console output → Set verbose=False
        - No output shown → Check verbose=True is set
        - Events still logged → History maintained regardless of verbose

    Examples:
        >>> # Production mode (quiet)
        >>> bus = create_default_event_bus()

        >>> # Development mode (with logging)
        >>> bus = create_default_event_bus(verbose=True)
        >>> bus.emit(EventType.AGENT_START, {"query": "test"}, agent_name="research")
        [agent_start] research: {'query': 'test'}

    Implements: REQ-CB-009 (create_default_event_bus)
    Spec: specs/callbacks-v1.0.md#section-5.1
    """
    # STEP 1: Create EventBus with default settings
    bus = EventBus()  # Default: 1000 event history

    # STEP 2: If verbose mode, register console logger for all event types
    if verbose:
        def log_event(event: Event):
            """Console logger callback - prints event in readable format."""
            agent = event.agent_name or "system"  # Default to "system" if no agent
            print(f"[{event.event_type.value}] {agent}: {event.data}")

        # STEP 3: Register logger for all event types
        for event_type in EventType:
            bus.on(event_type, log_event)

    # STEP 4: Return configured bus
    return bus

# Callbacks (Event System) Specification v1.0

**Spec Type**: Core System Component
**Constitutional Authority**: AGENTS.md Article III (Immutable Architecture)
**Status**: APPROVED
**Created**: 2025-12-05
**Last Updated**: 2025-12-05

---

## 1. PURPOSE

The Callbacks module provides a pub/sub event system for agent observability, enabling real-time monitoring, logging, and audit trails of agent operations.

**Design Goal**: Zero-overhead event system that never crashes parent process, with 1000-event history retained in memory.

**Analogy**: Like industrial SCADA (Supervisory Control And Data Acquisition) - monitors system state without affecting operations.

---

## 2. REQUIREMENTS

### 2.1 Event Types (REQ-CB-001)

**MUST** define standard event types as enum:

- **AGENT_START**: Agent begins processing query
- **AGENT_END**: Agent completes successfully
- **ROUTE_DECISION**: Orchestrator selects agent
- **ERROR**: Any error condition
- **TOOL_CALL**: Agent invokes a tool (future enhancement)

**MUST** support custom event types via string enum extension.

### 2.2 Event Structure (REQ-CB-002)

**Each event MUST contain**:
- `event_type`: EventType enum value
- `timestamp`: datetime object (UTC)
- `data`: Dict[str, Any] (event-specific payload)
- `agent_name`: Optional[str] (which agent emitted)

**MUST** provide `to_dict()` method for JSON serialization.

### 2.3 EventBus - Pub/Sub System (REQ-CB-003)

**MUST** implement publisher/subscriber pattern:
- Listeners register for specific event types
- Events emitted to all registered listeners
- Listeners are callbacks: `Callable[[Event], None]`
- Multiple listeners per event type supported

**MUST** isolate listener errors:
- Listener exception MUST NOT crash EventBus
- Listener exception MUST be logged
- Other listeners MUST still receive event

### 2.4 Event History (REQ-CB-004)

**MUST** store all events in chronological order.

**MUST** support configurable max history size (default 1000).

**MUST** implement circular buffer (oldest events dropped when full).

**MUST** support querying history with filters:
- By event_type
- By agent_name
- By limit (most recent N events)

**MUST** support clearing history manually.

### 2.5 Listener Management (REQ-CB-005)

**MUST** support registering listeners: `on(event_type, callback)`

**MUST** support unregistering listeners: `off(event_type, callback)`

**MUST** support multiple listeners per event type (all called).

**MUST** call listeners in registration order.

---

## 3. DATA STRUCTURES

### 3.1 EventType (Enum)

```python
class EventType(str, Enum):
    AGENT_START = "agent_start"
    AGENT_END = "agent_end"
    ROUTE_DECISION = "route_decision"
    ERROR = "error"
    TOOL_CALL = "tool_call"
```

### 3.2 Event (Dataclass)

```python
@dataclass
class Event:
    event_type: EventType
    timestamp: datetime           # UTC timezone
    data: Dict[str, Any]          # Event payload
    agent_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        # Returns JSON-serializable dict
```

### 3.3 EventBus (Class)

```python
class EventBus:
    _listeners: Dict[EventType, List[Callable[[Event], None]]]
    _history: List[Event]
    _max_history: int

    def __init__(self, max_history: int = 1000)
    def on(event_type: EventType, callback: Callable[[Event], None]) -> None
    def off(event_type: EventType, callback: Callable[[Event], None]) -> None
    def emit(event_type: EventType, data: Dict[str, Any],
             agent_name: Optional[str] = None) -> Event
    def get_history(event_type: Optional[EventType] = None,
                   agent_name: Optional[str] = None,
                   limit: int = 100) -> List[Event]
    def clear_history() -> None
```

---

## 4. BEHAVIORAL SPECIFICATIONS

### 4.1 emit() Behavior (REQ-CB-006)

**When emit() is called**:
1. Create Event object with current UTC timestamp
2. Append to history (drop oldest if history full)
3. Retrieve listeners for this event_type
4. Call each listener with Event object
5. If listener raises exception:
   - Log exception message
   - Continue to next listener
6. Return the Event object

**MUST NOT**:
- Block indefinitely
- Crash on listener errors
- Modify event after emission
- Lose events if listener fails

### 4.2 History Management (REQ-CB-007)

**Circular Buffer Behavior**:
- History list has fixed capacity (_max_history)
- When full and new event added:
  - Remove oldest event (index 0)
  - Append new event
- Maintains chronological order (oldest to newest)

**Query Behavior**:
- Filters applied in-memory (simple list comprehension)
- Returns most recent N events (tail of list)
- Empty list if no matches

### 4.3 Listener Isolation (REQ-CB-008)

**Each listener runs in try/except block**:
```python
for callback in listeners:
    try:
        callback(event)
    except Exception as e:
        print(f"[EventBus] Callback error: {e}")
        # Continue to next listener
```

**Guarantees**:
- One failing listener does not affect others
- Event always added to history (before listeners called)
- Exception logged but not propagated

---

## 5. CONVENIENCE FUNCTIONS

### 5.1 create_default_event_bus() (REQ-CB-009)

**Factory function** for common use case:

```python
def create_default_event_bus(verbose: bool = False) -> EventBus:
    """
    Create EventBus with optional console logging.

    If verbose=True, automatically logs all events to console:
    [event_type] agent_name: {data}
    """
```

**Behavior**:
- Creates EventBus instance
- If verbose=True:
  - Registers console logger for ALL event types
  - Format: `[{event_type}] {agent_name or 'system'}: {data}`
- Returns configured EventBus

**Use Case**: Quick setup for development/debugging

---

## 6. PERFORMANCE REQUIREMENTS

### 6.1 Event Emission Speed (REQ-CB-010)

- emit() must complete in <1ms average (excluding listener execution)
- History append is O(1) amortized
- Listener dispatch is O(n) where n = listener count
- No blocking I/O in EventBus core

### 6.2 Memory Constraints (REQ-CB-011)

- Default max_history = 1000 events
- Each event ~1KB average
- Max memory: ~1MB for history
- Configurable for high-throughput systems

---

## 7. ERROR HANDLING

### 7.1 Required Error Cases (REQ-CB-012)

**MUST** handle gracefully:
1. Listener raises exception → Log and continue
2. Listener blocks/hangs → Continue after timeout (Python default)
3. Invalid event_type → TypeError at emit() call
4. Empty listeners list → No-op (event still recorded)
5. History query with no matches → Return empty list

**MUST NOT**:
- Crash EventBus on listener error
- Lose events due to listener failures
- Allow memory leak (circular buffer enforced)

### 7.2 Logging Standards (REQ-CB-013)

**All internal errors logged to stdout**:
- Format: `[EventBus] {error_type}: {message}`
- Examples:
  - `[EventBus] Callback error: division by zero`
  - `[EventBus] History full, dropping oldest event`

**No exceptions propagated** from EventBus internals.

---

## 8. TESTING REQUIREMENTS

### 8.1 Unit Tests (REQ-CB-014)

**MUST** validate:
1. Event creation with all fields
2. Event.to_dict() serialization
3. EventBus registration (on/off)
4. Event emission calls listeners
5. Multiple listeners all receive event
6. Listener exception does not crash bus
7. History stores events chronologically
8. History respects max_history limit
9. History filtering by event_type works
10. History filtering by agent_name works
11. History limit parameter works
12. clear_history() empties history
13. create_default_event_bus() verbose logging

### 8.2 Integration Tests (REQ-CB-015)

**MUST** validate:
1. 1000+ event stress test (circular buffer)
2. Concurrent listener registration (thread safety not required v1.0)
3. Event history persistence across operations
4. Verbose mode console output formatting

---

## 9. DEPENDENCIES

### 9.1 Standard Library

- **dataclasses**: Event structure
- **datetime**: Timestamps (datetime.now())
- **enum**: EventType definition
- **typing**: Type hints (Dict, List, Any, Optional, Callable)

**NO external dependencies** - Pure Python stdlib only.

---

## 10. USAGE EXAMPLES

### 10.1 Basic Pub/Sub

```python
from agent_factory.core import EventBus, EventType

# Create bus
bus = EventBus()

# Register listener
received = []
bus.on(EventType.AGENT_START, lambda e: received.append(e))

# Emit event
bus.emit(EventType.AGENT_START, {"query": "test"}, agent_name="research")

# Check received
assert len(received) == 1
assert received[0].data["query"] == "test"
```

### 10.2 History Querying

```python
# Emit multiple events
bus.emit(EventType.AGENT_START, {}, agent_name="agent1")
bus.emit(EventType.AGENT_END, {}, agent_name="agent1")
bus.emit(EventType.AGENT_START, {}, agent_name="agent2")

# Query by type
starts = bus.get_history(event_type=EventType.AGENT_START)
assert len(starts) == 2

# Query by agent
agent1_events = bus.get_history(agent_name="agent1")
assert len(agent1_events) == 2
```

### 10.3 Verbose Mode for Debugging

```python
from agent_factory.core import create_default_event_bus, EventType

# Auto-logging bus
bus = create_default_event_bus(verbose=True)

# This will print to console:
# [agent_start] research: {'query': 'test'}
bus.emit(EventType.AGENT_START, {"query": "test"}, agent_name="research")
```

---

## 11. TROUBLESHOOTING

### Common Issues

**Issue**: Events not being received by listener
- Check: Listener registered before emit()
- Check: Event type matches exactly
- Solution: Use EventType enum, not string

**Issue**: Listener crashes entire program
- Check: Using EventBus (not raw callbacks)
- Check: EventBus version is v1.0+
- Solution: EventBus should isolate errors - file bug if not

**Issue**: History missing old events
- Check: max_history limit reached
- Check: clear_history() not called accidentally
- Solution: Increase max_history or implement persistent storage

**Issue**: Memory usage growing unbounded
- Check: max_history is set
- Check: Circular buffer implementation
- Solution: Default 1000-event limit should prevent this

---

## 12. FUTURE ENHANCEMENTS (Out of Scope v1.0)

- Thread-safe event bus (threading.Lock)
- Async event emission (asyncio support)
- Persistent event storage (SQLite, log files)
- Event filtering/transformation pipeline
- Event replay functionality
- Performance metrics (events/sec, listener latency)
- Remote event subscribers (websockets, gRPC)

---

## 13. SPEC COMPLIANCE VALIDATION

### 13.1 Acceptance Criteria

This specification is considered **implemented** when:

1. All REQ-CB-* requirements pass unit tests
2. Code contains PLC-style rung annotations referencing this spec
3. factory.py can regenerate callbacks.py from this spec
4. Integration with orchestrator (specs/orchestrator-v1.0.md) validated
5. 1000-event stress test passes without memory leak

### 13.2 Spec Version History

- **v1.0** (2025-12-05): Initial specification based on Phase 1 prototype

---

**END OF SPECIFICATION**

*This spec is the source of truth for event system behavior. Code is regenerable from this document.*

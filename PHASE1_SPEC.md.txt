# PHASE1_SPEC.md - Orchestration System

## Overview

Build multi-agent routing. One orchestrator receives queries, routes to specialist agents.

**Success:** Voice command "Check my calendar" routes to calendar_agent automatically.

---

## Files to Create
```
agent_factory/core/orchestrator.py    # Main orchestrator
agent_factory/core/callbacks.py       # Event system
agent_factory/examples/orchestrator_demo.py
tests/test_orchestrator.py
```

---

## 1. callbacks.py

Create `agent_factory/core/callbacks.py`:
```python
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
```

---

## 2. orchestrator.py

Create `agent_factory/core/orchestrator.py`:
```python
"""
Multi-agent orchestrator with hybrid routing.
Routes queries to specialist agents via keywords or LLM classification.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime
import time

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from .callbacks import EventBus, EventType, create_default_event_bus


@dataclass
class AgentRegistration:
    """Metadata for a registered agent."""
    name: str
    agent: Any  # LangChain agent
    keywords: List[str] = field(default_factory=list)
    description: str = ""
    priority: int = 0  # Higher = higher priority


@dataclass 
class RouteResult:
    """Result of routing decision."""
    agent_name: str
    method: str  # "keyword" or "llm"
    confidence: float
    response: Any = None
    error: Optional[str] = None
    duration_ms: Optional[float] = None


class AgentOrchestrator:
    """
    Routes queries to specialist agents.
    
    Pattern: Orchestrator routes, doesn't work.
    - Keyword matching first (fast, deterministic)
    - LLM classification fallback (flexible, slower)
    
    Usage:
        orchestrator = AgentOrchestrator(llm=my_llm)
        orchestrator.register("calendar", calendar_agent, keywords=["schedule", "meeting"])
        orchestrator.register("email", email_agent, keywords=["mail", "inbox"])
        
        result = orchestrator.route("What's on my schedule today?")
        # Routes to calendar agent
    """
    
    def __init__(
        self,
        llm: Optional[BaseChatModel] = None,
        event_bus: Optional[EventBus] = None,
        verbose: bool = False
    ):
        self._agents: Dict[str, AgentRegistration] = {}
        self._llm = llm
        self._event_bus = event_bus or create_default_event_bus(verbose)
        self._verbose = verbose
        self._fallback_agent: Optional[str] = None
    
    @property
    def event_bus(self) -> EventBus:
        """Access event bus for external subscriptions."""
        return self._event_bus
    
    def register(
        self,
        name: str,
        agent: Any,
        keywords: Optional[List[str]] = None,
        description: str = "",
        priority: int = 0,
        is_fallback: bool = False
    ) -> None:
        """
        Register an agent with the orchestrator.
        
        Args:
            name: Unique identifier for the agent
            agent: LangChain agent instance
            keywords: Words that trigger this agent (case-insensitive)
            description: Human-readable description for LLM classification
            priority: Higher priority wins ties (default 0)
            is_fallback: Use this agent when no match found
        """
        if name in self._agents:
            raise ValueError(f"Agent '{name}' already registered")
        
        self._agents[name] = AgentRegistration(
            name=name,
            agent=agent,
            keywords=[k.lower() for k in (keywords or [])],
            description=description or f"Agent: {name}",
            priority=priority
        )
        
        if is_fallback:
            self._fallback_agent = name
        
        if self._verbose:
            print(f"[Orchestrator] Registered: {name} (keywords: {keywords})")
    
    def unregister(self, name: str) -> None:
        """Remove an agent from the orchestrator."""
        if name in self._agents:
            del self._agents[name]
            if self._fallback_agent == name:
                self._fallback_agent = None
    
    def list_agents(self) -> List[str]:
        """Return list of registered agent names."""
        return list(self._agents.keys())
    
    def get_agent(self, name: str) -> Optional[Any]:
        """Get agent by name."""
        reg = self._agents.get(name)
        return reg.agent if reg else None
    
    def _match_keywords(self, query: str) -> Optional[AgentRegistration]:
        """
        Find agent by keyword matching.
        Returns highest priority match.
        """
        query_lower = query.lower()
        matches: List[AgentRegistration] = []
        
        for reg in self._agents.values():
            for keyword in reg.keywords:
                if keyword in query_lower:
                    matches.append(reg)
                    break
        
        if not matches:
            return None
        
        # Return highest priority
        return max(matches, key=lambda r: r.priority)
    
    def _classify_with_llm(self, query: str) -> Optional[AgentRegistration]:
        """
        Use LLM to classify query when keywords don't match.
        """
        if not self._llm:
            return None
        
        if not self._agents:
            return None
        
        # Build agent descriptions
        agent_list = "\n".join([
            f"- {name}: {reg.description}"
            for name, reg in self._agents.items()
        ])
        
        system_prompt = f"""You are a query router. Given a user query, select the most appropriate agent.

Available agents:
{agent_list}

Respond with ONLY the agent name, nothing else. If no agent fits, respond with "NONE"."""

        try:
            response = self._llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=query)
            ])
            
            agent_name = response.content.strip()
            
            if agent_name == "NONE":
                return None
            
            return self._agents.get(agent_name)
            
        except Exception as e:
            self._event_bus.emit(
                EventType.ERROR,
                {"error_type": "llm_classification", "message": str(e)}
            )
            return None
    
    def route(self, query: str) -> RouteResult:
        """
        Route query to appropriate agent and execute.
        
        Routing order:
        1. Keyword match (fast, deterministic)
        2. LLM classification (flexible)
        3. Fallback agent (if configured)
        4. Error response
        
        Returns:
            RouteResult with agent response or error
        """
        start_time = time.time()
        
        # Try keyword matching first
        matched = self._match_keywords(query)
        method = "keyword"
        confidence = 1.0
        
        # Fall back to LLM
        if not matched:
            matched = self._classify_with_llm(query)
            method = "llm"
            confidence = 0.8  # LLM classification is less certain
        
        # Fall back to fallback agent
        if not matched and self._fallback_agent:
            matched = self._agents.get(self._fallback_agent)
            method = "fallback"
            confidence = 0.5
        
        # No match at all
        if not matched:
            return RouteResult(
                agent_name="",
                method="none",
                confidence=0.0,
                error="No agent found for query"
            )
        
        # Emit routing decision
        self._event_bus.emit(
            EventType.ROUTE_DECISION,
            {
                "query": query,
                "matched_agent": matched.name,
                "method": method,
                "confidence": confidence
            }
        )
        
        # Execute agent
        try:
            self._event_bus.emit(
                EventType.AGENT_START,
                {"query": query},
                agent_name=matched.name
            )
            
            # Invoke the agent
            response = matched.agent.invoke({"input": query})
            
            duration_ms = (time.time() - start_time) * 1000
            
            self._event_bus.emit(
                EventType.AGENT_END,
                {"output": str(response), "duration_ms": duration_ms},
                agent_name=matched.name
            )
            
            return RouteResult(
                agent_name=matched.name,
                method=method,
                confidence=confidence,
                response=response,
                duration_ms=duration_ms
            )
            
        except Exception as e:
            self._event_bus.emit(
                EventType.ERROR,
                {"error_type": "agent_execution", "message": str(e)},
                agent_name=matched.name
            )
            
            return RouteResult(
                agent_name=matched.name,
                method=method,
                confidence=confidence,
                error=str(e)
            )
    
    def route_to(self, agent_name: str, query: str) -> RouteResult:
        """
        Route directly to a specific agent (bypass routing).
        Useful for testing or explicit routing.
        """
        if agent_name not in self._agents:
            return RouteResult(
                agent_name=agent_name,
                method="direct",
                confidence=0.0,
                error=f"Agent '{agent_name}' not found"
            )
        
        matched = self._agents[agent_name]
        start_time = time.time()
        
        try:
            self._event_bus.emit(
                EventType.AGENT_START,
                {"query": query},
                agent_name=agent_name
            )
            
            response = matched.agent.invoke({"input": query})
            duration_ms = (time.time() - start_time) * 1000
            
            self._event_bus.emit(
                EventType.AGENT_END,
                {"output": str(response), "duration_ms": duration_ms},
                agent_name=agent_name
            )
            
            return RouteResult(
                agent_name=agent_name,
                method="direct",
                confidence=1.0,
                response=response,
                duration_ms=duration_ms
            )
            
        except Exception as e:
            self._event_bus.emit(
                EventType.ERROR,
                {"error_type": "agent_execution", "message": str(e)},
                agent_name=agent_name
            )
            
            return RouteResult(
                agent_name=agent_name,
                method="direct",
                confidence=1.0,
                error=str(e)
            )
```

---

## 3. Update __init__.py

Update `agent_factory/core/__init__.py` to include new imports:
```python
from .agent_factory import AgentFactory
from .orchestrator import AgentOrchestrator, RouteResult, AgentRegistration
from .callbacks import EventBus, EventType, Event, create_default_event_bus

__all__ = [
    "AgentFactory",
    "AgentOrchestrator",
    "RouteResult", 
    "AgentRegistration",
    "EventBus",
    "EventType",
    "Event",
    "create_default_event_bus"
]
```

---

## 4. Update AgentFactory

Add method to `agent_factory/core/agent_factory.py`:
```python
# Add this import at top
from .orchestrator import AgentOrchestrator
from .callbacks import EventBus, create_default_event_bus

# Add this method to AgentFactory class
def create_orchestrator(
    self,
    event_bus: Optional[EventBus] = None,
    verbose: Optional[bool] = None
) -> AgentOrchestrator:
    """
    Create an orchestrator for multi-agent routing.
    
    Args:
        event_bus: Optional shared event bus
        verbose: Override factory verbose setting
        
    Returns:
        AgentOrchestrator configured with factory's LLM
    """
    llm = self._get_default_llm()
    
    return AgentOrchestrator(
        llm=llm,
        event_bus=event_bus,
        verbose=verbose if verbose is not None else self.verbose
    )
```

---

## 5. Demo Script

Create `agent_factory/examples/orchestrator_demo.py`:
```python
"""
Orchestrator Demo - Multi-agent routing
"""
import os
import sys

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from agent_factory.core import AgentFactory, EventType


def main():
    print("=" * 60)
    print("ORCHESTRATOR DEMO")
    print("=" * 60)
    
    # Create factory
    factory = AgentFactory(verbose=True)
    
    # Create specialist agents
    research_agent = factory.create_agent(
        role="Research Specialist",
        tools_list=[],
        system_prompt="You are a research assistant. Answer questions about facts and information."
    )
    
    creative_agent = factory.create_agent(
        role="Creative Writer",
        tools_list=[],
        system_prompt="You are a creative writer. Help with stories, poems, and creative content."
    )
    
    code_agent = factory.create_agent(
        role="Code Assistant", 
        tools_list=[],
        system_prompt="You are a coding assistant. Help with programming questions."
    )
    
    # Create orchestrator
    orchestrator = factory.create_orchestrator(verbose=True)
    
    # Register agents with keywords
    orchestrator.register(
        "research",
        research_agent,
        keywords=["search", "find", "what is", "who is", "explain"],
        description="Answers factual questions and does research"
    )
    
    orchestrator.register(
        "creative",
        creative_agent,
        keywords=["write", "story", "poem", "creative"],
        description="Helps with creative writing and content"
    )
    
    orchestrator.register(
        "coding",
        code_agent,
        keywords=["code", "python", "function", "bug", "programming"],
        description="Helps with programming and code",
        is_fallback=True  # Default when nothing matches
    )
    
    # Subscribe to events
    def on_route(event):
        print(f"\n>>> ROUTE: {event.data['query'][:50]}...")
        print(f"    Agent: {event.data['matched_agent']}")
        print(f"    Method: {event.data['method']}")
    
    def on_complete(event):
        print(f"<<< COMPLETE: {event.agent_name} ({event.data['duration_ms']:.0f}ms)")
    
    orchestrator.event_bus.on(EventType.ROUTE_DECISION, on_route)
    orchestrator.event_bus.on(EventType.AGENT_END, on_complete)
    
    # Test queries
    print("\n" + "-" * 60)
    print("REGISTERED AGENTS:", orchestrator.list_agents())
    print("-" * 60)
    
    test_queries = [
        "What is the capital of France?",        # Should route to research
        "Write me a short poem about coding",    # Should route to creative  
        "How do I write a for loop in Python?",  # Should route to coding
        "Tell me something interesting",         # Should fall back to coding
    ]
    
    for query in test_queries:
        print(f"\n{'=' * 60}")
        print(f"QUERY: {query}")
        print("=" * 60)
        
        result = orchestrator.route(query)
        
        if result.error:
            print(f"ERROR: {result.error}")
        else:
            # Extract response text
            if hasattr(result.response, 'get'):
                output = result.response.get('output', str(result.response))
            else:
                output = str(result.response)
            
            # Truncate for display
            if len(output) > 200:
                output = output[:200] + "..."
            
            print(f"\nRESPONSE:\n{output}")
    
    # Show event history
    print(f"\n{'=' * 60}")
    print("EVENT HISTORY SUMMARY")
    print("=" * 60)
    
    history = orchestrator.event_bus.get_history()
    print(f"Total events: {len(history)}")
    
    for event_type in EventType:
        count = len([e for e in history if e.event_type == event_type])
        if count > 0:
            print(f"  {event_type.value}: {count}")
    
    print("\nDemo complete!")


if __name__ == "__main__":
    main()
```

---

## 6. Tests

Create `tests/test_orchestrator.py`:
```python
"""Tests for orchestrator system."""
import pytest
from unittest.mock import MagicMock, patch

from agent_factory.core.callbacks import EventBus, EventType, Event
from agent_factory.core.orchestrator import AgentOrchestrator, RouteResult


class TestEventBus:
    """Tests for EventBus."""
    
    def test_emit_and_receive(self):
        """Events are received by listeners."""
        bus = EventBus()
        received = []
        
        bus.on(EventType.AGENT_START, lambda e: received.append(e))
        bus.emit(EventType.AGENT_START, {"query": "test"})
        
        assert len(received) == 1
        assert received[0].data["query"] == "test"
    
    def test_multiple_listeners(self):
        """Multiple listeners receive same event."""
        bus = EventBus()
        count = [0]
        
        bus.on(EventType.AGENT_START, lambda e: count.__setitem__(0, count[0] + 1))
        bus.on(EventType.AGENT_START, lambda e: count.__setitem__(0, count[0] + 1))
        bus.emit(EventType.AGENT_START, {})
        
        assert count[0] == 2
    
    def test_history(self):
        """Events are stored in history."""
        bus = EventBus()
        
        bus.emit(EventType.AGENT_START, {"a": 1})
        bus.emit(EventType.AGENT_END, {"b": 2})
        
        history = bus.get_history()
        assert len(history) == 2
    
    def test_history_filter(self):
        """History can be filtered by type."""
        bus = EventBus()
        
        bus.emit(EventType.AGENT_START, {})
        bus.emit(EventType.AGENT_END, {})
        bus.emit(EventType.AGENT_START, {})
        
        starts = bus.get_history(event_type=EventType.AGENT_START)
        assert len(starts) == 2


class TestOrchestrator:
    """Tests for AgentOrchestrator."""
    
    def test_register_agent(self):
        """Agents can be registered."""
        orch = AgentOrchestrator()
        mock_agent = MagicMock()
        
        orch.register("test", mock_agent, keywords=["hello"])
        
        assert "test" in orch.list_agents()
    
    def test_duplicate_registration_fails(self):
        """Duplicate names raise error."""
        orch = AgentOrchestrator()
        mock_agent = MagicMock()
        
        orch.register("test", mock_agent)
        
        with pytest.raises(ValueError):
            orch.register("test", mock_agent)
    
    def test_keyword_routing(self):
        """Queries route by keyword."""
        orch = AgentOrchestrator()
        
        agent1 = MagicMock()
        agent1.invoke.return_value = {"output": "response1"}
        
        agent2 = MagicMock()
        agent2.invoke.return_value = {"output": "response2"}
        
        orch.register("agent1", agent1, keywords=["hello", "hi"])
        orch.register("agent2", agent2, keywords=["bye", "goodbye"])
        
        result = orch.route("hello there")
        
        assert result.agent_name == "agent1"
        assert result.method == "keyword"
        agent1.invoke.assert_called_once()
    
    def test_priority_routing(self):
        """Higher priority wins ties."""
        orch = AgentOrchestrator()
        
        low_priority = MagicMock()
        high_priority = MagicMock()
        high_priority.invoke.return_value = {"output": "high"}
        
        orch.register("low", low_priority, keywords=["test"], priority=1)
        orch.register("high", high_priority, keywords=["test"], priority=10)
        
        result = orch.route("test query")
        
        assert result.agent_name == "high"
    
    def test_fallback_agent(self):
        """Fallback used when no match."""
        orch = AgentOrchestrator()
        
        fallback = MagicMock()
        fallback.invoke.return_value = {"output": "fallback"}
        
        orch.register("fallback", fallback, is_fallback=True)
        
        result = orch.route("random unmatched query")
        
        assert result.agent_name == "fallback"
        assert result.method == "fallback"
    
    def test_no_match_error(self):
        """Error returned when nothing matches."""
        orch = AgentOrchestrator()
        
        result = orch.route("query with no agents")
        
        assert result.error is not None
        assert "No agent found" in result.error
    
    def test_events_emitted(self):
        """Events are emitted during routing."""
        orch = AgentOrchestrator()
        events = []
        
        orch.event_bus.on(EventType.ROUTE_DECISION, lambda e: events.append(e))
        orch.event_bus.on(EventType.AGENT_START, lambda e: events.append(e))
        orch.event_bus.on(EventType.AGENT_END, lambda e: events.append(e))
        
        agent = MagicMock()
        agent.invoke.return_value = {"output": "test"}
        orch.register("test", agent, keywords=["hello"])
        
        orch.route("hello")
        
        event_types = [e.event_type for e in events]
        assert EventType.ROUTE_DECISION in event_types
        assert EventType.AGENT_START in event_types
        assert EventType.AGENT_END in event_types


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

---

## Validation Commands

After each file is created, run:
```bash
# After callbacks.py
poetry run python -c "from agent_factory.core.callbacks import EventBus; print('PASS: callbacks')"

# After orchestrator.py
poetry run python -c "from agent_factory.core.orchestrator import AgentOrchestrator; print('PASS: orchestrator')"

# After __init__.py update
poetry run python -c "from agent_factory.core import AgentOrchestrator, EventBus; print('PASS: imports')"

# After AgentFactory update
poetry run python -c "from agent_factory.core import AgentFactory; f = AgentFactory(); print('PASS: factory')"

# After demo
poetry run python agent_factory/examples/orchestrator_demo.py

# After tests
poetry run pytest tests/test_orchestrator.py -v
```

---

## Success Criteria

Phase 1 is complete when:

1. All validation commands pass
2. Demo runs and shows routing to different agents
3. Events are logged during execution
4. Tests pass
5. Code committed with tag `phase-1-complete`

---

## Behavior Specifications

### Priority
- Higher number = higher priority
- Default priority = 0
- Used for tie-breaking when multiple keywords match

### No Match Behavior
- Returns `RouteResult` with `error="No agent found for query"`
- Does not raise exception

### LLM Classification
- Only used when keyword matching fails
- Uses factory's default LLM
- Returns `None` if LLM unavailable or returns "NONE"

### Events
| Event | When | Data |
|-------|------|------|
| `route_decision` | After routing logic | query, matched_agent, method, confidence |
| `agent_start` | Before agent.invoke() | query |
| `agent_end` | After successful invoke | output, duration_ms |
| `error` | On any error | error_type, message |
```

---

Save this as `docs/PHASE1_SPEC.md` in your Agent Factory project.

Then tell Claude CLI:
```
I've added PHASE1_SPEC.md to docs/. Please read it and begin implementation starting with the first unchecked item in PROGRESS.md.
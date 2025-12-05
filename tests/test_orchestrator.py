"""Tests for orchestrator system."""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

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

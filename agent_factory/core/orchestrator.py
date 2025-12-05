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

"""
Orchestrator - Multi-Agent Routing System

PURPOSE:
    Routes user queries to the most appropriate specialist agent from a pool of registered agents.
    Like a PLC master controller deciding which robot/station handles each job on an assembly line.

Generated from: specs/orchestrator-v1.0.md
Generated on: 2025-12-05
Spec SHA256: orchestrator-hash

REGENERATION: python factory.py specs/orchestrator-v1.0.md

WHAT THIS DOES:
    Routes queries to specialist agents using hybrid logic:
    1. Keyword matching (fast, deterministic) - like limit switch triggering
    2. LLM classification (flexible, intelligent) - like vision system routing
    3. Fallback agent (graceful degradation) - like emergency backup station

WHY WE NEED THIS:
    - Single agent can't be expert at everything (research vs coding vs calendar)
    - Routing reduces cost (only run expensive agents when needed)
    - Enables modular agent development (each does one thing well)
    - Provides observability (track which agents handle what queries)

PLC ANALOGY:
    Like a PLC routing parts to different workstations:
    - Part sensor detects type (keyword matching)
    - Vision system classifies if uncertain (LLM classification)
    - Default station handles unknowns (fallback agent)
    - Every part gets processed somewhere (graceful degradation)
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable, Union
from datetime import datetime
import time

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, ValidationError

from .callbacks import EventBus, EventType, create_default_event_bus


@dataclass
class AgentRegistration:
    """
    Metadata for a registered agent.

    PURPOSE:
        Stores configuration and metadata for one specialist agent in the orchestrator's registry.
        Like a recipe card for a PLC workstation - stores what it does and when to use it.

    WHAT THIS STORES:
        - name: Unique identifier (e.g., "calendar_agent", "research_agent")
        - agent: The actual LangChain AgentExecutor instance
        - keywords: Trigger words that route queries here (e.g., ["schedule", "meeting"])
        - description: Human-readable purpose for LLM classification
        - priority: Tie-breaker when multiple agents match (higher = preferred)

    WHY WE NEED THIS:
        - Decouples agent registration from routing logic
        - Enables priority-based routing (some agents better than others)
        - Supports both keyword and LLM-based routing
        - Clean separation of concerns (data vs behavior)

    PLC ANALOGY:
        Like a workstation configuration record:
        - name = Station ID (e.g., "WELD_1", "PAINT_2")
        - agent = The actual hardware/robot at that station
        - keywords = Part types this station handles
        - priority = Preferred station when multiple options available

    Implements: REQ-ORCH-001 (Agent Registration)
    Spec: specs/orchestrator-v1.0.md#section-3.1
    """
    name: str                          # Unique identifier (e.g., "calendar_agent")
    agent: Any                         # LangChain AgentExecutor instance
    keywords: List[str] = field(default_factory=list)  # Trigger words (lowercase)
    description: str = ""              # Human-readable purpose for LLM
    priority: int = 0                  # Tie-breaker (higher = preferred)


@dataclass
class RouteResult:
    """
    Result of routing operation.

    PURPOSE:
        Encapsulates the complete result of routing and executing a query.
        Like a PLC job completion report - which station processed it, how long, any errors.

    WHAT THIS CONTAINS:
        - agent_name: Which agent handled the query (e.g., "calendar_agent")
        - method: How routing decision was made ("keyword" | "llm" | "fallback" | "direct")
        - confidence: How certain we are about routing (0.0-1.0)
        - response: Agent's actual output (dict, Pydantic model, or None)
        - error: Error message if execution failed
        - duration_ms: How long execution took (milliseconds)
        - trace_id: For observability/debugging (Phase 3+)

    WHY WE NEED THIS:
        - Provides transparency (caller knows which agent ran and why)
        - Enables monitoring (track confidence, duration, errors)
        - Supports debugging (trace_id links to observability)
        - Type-safe response handling (Pydantic schema validation)

    RESPONSE TYPES:
        The response field can be:
        - Raw dict (default, backwards compatible)
        - Pydantic BaseModel instance (if agent has response_schema)
        - None (if error occurred)

    PLC ANALOGY:
        Like a workstation completion report:
        - agent_name = Which station processed the part
        - method = How routing decision was made (sensor vs vision vs manual)
        - confidence = How certain we are it went to right station
        - response = Output product from station
        - error = Fault message if station failed
        - duration_ms = Cycle time for this part
        - trace_id = Lot/batch number for traceability

    Implements: REQ-ORCH-004 (Agent Execution)
    Spec: specs/orchestrator-v1.0.md#section-3.2
    """
    agent_name: str                    # Which agent handled query
    method: str                        # "keyword" | "llm" | "fallback" | "direct"
    confidence: float                  # 0.0-1.0 routing confidence
    response: Union[Dict[str, Any], BaseModel, None] = None  # Agent output
    error: Optional[str] = None        # Error message if failed
    duration_ms: Optional[float] = None  # Execution time (milliseconds)
    trace_id: Optional[str] = None     # Trace ID for observability


class AgentOrchestrator:
    """
    Multi-agent routing system with hybrid matching.

    PURPOSE:
        Routes incoming queries to the most appropriate specialist agent from a pool.
        Like a PLC master controller that decides which workstation handles each job.

    WHAT THIS DOES:
        1. Maintains registry of specialist agents (calendar, research, coding, etc.)
        2. Routes queries using 3-tier priority system:
           - Tier 1: Keyword matching (fast, deterministic, like limit switch)
           - Tier 2: LLM classification (flexible, like vision system)
           - Tier 3: Fallback agent (graceful degradation, like default station)
        3. Executes matched agent and returns structured result
        4. Emits events for observability (monitoring, debugging)
        5. Tracks costs, latency, success rates (Phase 3+)

    WHY WE NEED THIS:
        - No single agent can be expert at everything
        - Routing reduces cost (only use expensive agents when needed)
        - Enables modular development (each agent does one thing well)
        - Provides observability (which agent handled what, how long, errors)
        - Graceful degradation (fallback when no match)

    ROUTING DECISION FLOW:
        Query → Try keywords → Found? → Execute
                     ↓ No
                 Try LLM classify → Found? → Execute
                     ↓ No
                 Try fallback → Found? → Execute
                     ↓ No
                 Return error (no agent available)

    PLC ANALOGY:
        Like a PLC master controller for assembly line:
        - _agents = Registry of workstations (WELD_1, PAINT_2, TEST_3)
        - route() = Routing logic (which station handles this part?)
        - Keywords = Part type sensors (detect based on part features)
        - LLM = Vision system (classify complex/ambiguous parts)
        - Fallback = Default station (when part type unknown)
        - Events = HMI logging (track what happened, when, errors)

    Implements: REQ-ORCH-003 through REQ-ORCH-009
    Spec: specs/orchestrator-v1.0.md

    Attributes:
        _agents: Registry of registered agents
        _llm: Optional LLM for classification fallback
        _event_bus: Event system for observability
        _fallback_agent: Agent name to use when no match

    Examples:
        >>> orch = AgentOrchestrator(llm=my_llm)
        >>> orch.register("calendar", agent, keywords=["schedule", "meeting"])
        >>> result = orch.route("What's on my schedule?")
        >>> result.agent_name
        'calendar'
    """

    def __init__(
        self,
        llm: Optional[BaseChatModel] = None,
        event_bus: Optional[EventBus] = None,
        verbose: bool = False,
        enable_observability: bool = True
    ):
        """
        Initialize the orchestrator.

        PURPOSE:
            Sets up the orchestrator with empty registry and optional observability.
            Like initializing a PLC master controller before loading station configs.

        WHAT THIS DOES:
            1. Creates empty agent registry (Dict)
            2. Stores LLM reference (for fallback classification)
            3. Creates or attaches event bus (for monitoring)
            4. Initializes observability tools if enabled (Tracer, Metrics, CostTracker)

        WHY WE NEED THIS:
            - Centralized initialization prevents scattered setup code
            - Optional observability (can disable for testing/dev)
            - Event bus enables monitoring without tight coupling

        INPUTS:
            llm: Optional LLM for intelligent classification when keywords don't match
            event_bus: Optional shared event bus (creates default if None)
            verbose: Print routing decisions to console (useful for debugging)
            enable_observability: Enable tracing/metrics/cost tracking (Phase 3+)

        PLC ANALOGY:
            Like PLC master controller initialization:
            - llm = Vision system connection (optional, for complex routing)
            - event_bus = HMI/SCADA connection (for monitoring)
            - verbose = Debug mode (print to console)
            - enable_observability = Data logging enabled/disabled

        EDGE CASES:
            - llm=None: LLM classification disabled, only keywords and fallback work
            - event_bus=None: Creates default event bus (still works, just isolated)
            - enable_observability=False: No tracing/metrics (faster, for testing)
        """
        # STEP 1: Initialize empty agent registry (like PLC station table)
        self._agents: Dict[str, AgentRegistration] = {}

        # STEP 2: Store LLM reference for classification (can be None)
        self._llm = llm

        # STEP 3: Create or attach event bus for monitoring
        self._event_bus = event_bus or create_default_event_bus(verbose)
        self._verbose = verbose

        # STEP 4: Initialize fallback agent (none yet, set via register(..., is_fallback=True))
        self._fallback_agent: Optional[str] = None

        # STEP 5: Set up observability tools if enabled (Phase 3+)
        self._enable_observability = enable_observability
        if enable_observability:
            from agent_factory.observability import Tracer, Metrics, CostTracker
            self.tracer = Tracer()           # For distributed tracing
            self.metrics = Metrics()         # For latency/success metrics
            self.cost_tracker = CostTracker()  # For API cost tracking
        else:
            # Observability disabled (faster for testing)
            self.tracer = None
            self.metrics = None
            self.cost_tracker = None

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

        PURPOSE:
            Adds a specialist agent to the orchestrator's routing registry.
            Like adding a new workstation to the PLC master controller's routing table.

        WHAT THIS DOES:
            1. Validates name is unique (no duplicates allowed)
            2. Creates AgentRegistration record with metadata
            3. Normalizes keywords to lowercase (for case-insensitive matching)
            4. Optionally sets as fallback agent
            5. Logs registration if verbose mode enabled

        WHY WE NEED THIS:
            - Orchestrator needs to know what agents exist and when to use them
            - Keywords enable fast deterministic routing (no LLM needed)
            - Priority handles conflicts (multiple agents match same keywords)
            - Fallback provides graceful degradation (always works)

        INPUTS:
            name: Unique identifier (e.g., "calendar_agent", "research_agent")
            agent: LangChain AgentExecutor instance (the actual agent)
            keywords: Trigger words for this agent (e.g., ["schedule", "meeting", "calendar"])
            description: Human-readable purpose for LLM classification
            priority: Tie-breaker when multiple agents match (higher = preferred, default 0)
            is_fallback: Mark as fallback agent (handles queries when no other match)

        OUTPUTS:
            None (modifies self._agents registry in-place)

        EDGE CASES:
            - name already registered → Raises ValueError (prevents overwriting)
            - keywords=None → Empty list (agent only reachable via LLM or direct)
            - description="" → Auto-generates "Agent: {name}"
            - is_fallback=True → Sets this agent as fallback (replaces previous if any)

        TROUBLESHOOTING:
            - "Agent already registered" → Use different name or unregister first
            - Agent not routing → Check keywords match query terms
            - Wrong agent routing → Check priority values (higher wins)

        PLC ANALOGY:
            Like registering a workstation in PLC routing table:
            - name = Station ID (e.g., "WELD_1")
            - agent = The actual hardware/robot at that station
            - keywords = Part types this station handles (e.g., ["metal", "bracket"])
            - priority = Preferred station when multiple options
            - is_fallback = Backup station when primary unavailable

        Examples:
            >>> orch.register("calendar", cal_agent, keywords=["schedule", "meeting"])
            >>> orch.register("research", res_agent, keywords=["search", "find"], priority=10)
            >>> orch.register("general", gen_agent, is_fallback=True)
        """
        # STEP 1: Validate name is unique (prevent overwriting existing agents)
        if name in self._agents:
            raise ValueError(f"Agent '{name}' already registered")

        # STEP 2: Create registration record with normalized keywords
        self._agents[name] = AgentRegistration(
            name=name,
            agent=agent,
            keywords=[k.lower() for k in (keywords or [])],  # Normalize to lowercase
            description=description or f"Agent: {name}",     # Auto-description if empty
            priority=priority
        )

        # STEP 3: Set as fallback if requested (replaces previous fallback)
        if is_fallback:
            self._fallback_agent = name

        # STEP 4: Log registration if verbose mode (debugging aid)
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

    def _parse_response(
        self,
        response: Any,
        agent: Any
    ) -> Union[Dict[str, Any], BaseModel]:
        """
        Parse agent response into structured format if schema is defined.

        Args:
            response: Raw agent response
            agent: Agent that generated the response

        Returns:
            Either the raw response (dict) or a validated Pydantic model instance
        """
        # Check if agent has a response schema
        response_schema = getattr(agent, 'metadata', {}).get('response_schema')

        if not response_schema:
            # No schema defined, return raw response
            return response

        # Try to parse response into schema
        try:
            # Extract output from response dict
            if isinstance(response, dict):
                output_text = response.get('output', str(response))
            else:
                output_text = str(response)

            # Create schema instance with parsed data
            # For now, we'll create a basic instance with success=True and output
            # More sophisticated parsing can be added later
            schema_instance = response_schema(
                success=True,
                output=output_text,
                metadata={}
            )
            return schema_instance

        except (ValidationError, TypeError, AttributeError) as e:
            # Schema parsing failed, return raw response
            # Could emit error event here
            if self._verbose:
                print(f"[Orchestrator] Schema validation failed: {e}")
            return response

    def _match_keywords(self, query: str) -> Optional[AgentRegistration]:
        """
        Find agent by keyword matching (fast, deterministic routing).

        PURPOSE:
            Uses simple substring matching to route queries - fastest routing method.
            Like a PLC limit switch detecting part type by physical features.

        WHAT THIS DOES:
            1. Converts query to lowercase (case-insensitive matching)
            2. Checks each agent's keywords against query
            3. Collects all matching agents
            4. Returns highest priority match (or None if no matches)

        WHY WE NEED THIS:
            - Fastest routing method (no LLM call, <1ms)
            - Deterministic (same query always routes to same agent)
            - Zero cost (no API usage)
            - Reliable for common patterns (e.g., "schedule" → calendar agent)

        INPUTS:
            query: User's query string (e.g., "What's my schedule tomorrow?")

        OUTPUTS:
            AgentRegistration of highest priority match, or None if no keywords match

        EDGE CASES:
            - Empty query → No match (returns None)
            - Multiple agents match → Returns highest priority
            - Tie on priority → Returns arbitrary match (use priority to disambiguate)
            - Keyword is substring → Matches (e.g., "schedule" matches "rescheduled")

        TROUBLESHOOTING:
            - Query not routing → Check if query contains any registered keywords
            - Wrong agent routing → Check priority values or keyword specificity
            - Case sensitivity issues → Already handled (query.lower())

        PLC ANALOGY:
            Like a PLC sensor-based routing:
            - query = Part passing by sensor
            - keywords = Features sensor looks for (size, color, weight)
            - matches = All stations that could handle this part
            - priority = Preferred station when multiple options
        """
        # STEP 1: Normalize query to lowercase for case-insensitive matching
        query_lower = query.lower()
        matches: List[AgentRegistration] = []

        # STEP 2: Check each agent's keywords against query
        for reg in self._agents.values():
            for keyword in reg.keywords:
                if keyword in query_lower:
                    # STEP 3: Found match - add to list and move to next agent
                    matches.append(reg)
                    break  # Don't check remaining keywords for this agent

        # STEP 4: Return None if no matches found
        if not matches:
            return None

        # STEP 5: Return highest priority match (tie-breaker)
        return max(matches, key=lambda r: r.priority)

    def _classify_with_llm(self, query: str) -> Optional[AgentRegistration]:
        """
        Use LLM to classify query when keywords don't match (intelligent routing).

        PURPOSE:
            Uses LLM to intelligently route ambiguous queries when keywords fail.
            Like a PLC vision system classifying complex parts that sensors can't detect.

        WHAT THIS DOES:
            1. Checks if LLM is configured (returns None if not)
            2. Builds list of available agents with descriptions
            3. Sends query + agent list to LLM for classification
            4. Parses LLM response to get agent name
            5. Returns matched agent or None if LLM says "NONE"

        WHY WE NEED THIS:
            - Handles queries without obvious keywords (e.g., "Help me plan my day")
            - Provides flexibility for natural language queries
            - Fallback when keyword matching fails
            - Enables semantic understanding (not just keyword matching)

        INPUTS:
            query: User's query string (e.g., "I need to organize my tasks")

        OUTPUTS:
            AgentRegistration if LLM finds match, else None

        EDGE CASES:
            - self._llm=None → Returns None (LLM not configured)
            - No agents registered → Returns None
            - LLM returns "NONE" → Returns None (no appropriate agent)
            - LLM returns invalid name → Returns None (agent not found)
            - LLM API error → Emits error event, returns None

        TROUBLESHOOTING:
            - LLM routing failing → Check agent descriptions are clear
            - Wrong agent selected → Improve agent descriptions
            - Timeout errors → LLM may be overloaded, use fallback
            - Cost too high → Reduce to LLM calls, rely more on keywords

        PLC ANALOGY:
            Like a PLC vision system for complex routing:
            - query = Part image captured by camera
            - agent_list = Known part types vision system can identify
            - LLM = Vision processing algorithm (classifies part)
            - response = Vision system's classification result
            - Fallback to None = Part type unknown, send to default station

        PERFORMANCE:
            - Latency: ~500ms-2s (depends on LLM)
            - Cost: ~$0.001-0.01 per query (depends on model)
            - Accuracy: High for well-described agents
        """
        # STEP 1: Check if LLM is configured (early exit if not)
        if not self._llm:
            return None  # LLM not available, can't classify

        # STEP 2: Check if any agents registered (early exit if empty)
        if not self._agents:
            return None  # No agents to route to

        # STEP 3: Build list of available agents with descriptions for LLM
        agent_list = "\n".join([
            f"- {name}: {reg.description}"
            for name, reg in self._agents.items()
        ])

        # STEP 4: Construct system prompt for LLM classification
        system_prompt = f"""You are a query router. Given a user query, select the most appropriate agent.

Available agents:
{agent_list}

Respond with ONLY the agent name, nothing else. If no agent fits, respond with "NONE"."""

        # STEP 5: Call LLM to classify query
        try:
            response = self._llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=query)
            ])

            # STEP 6: Extract agent name from LLM response
            agent_name = response.content.strip()

            # STEP 7: Handle "NONE" response (no appropriate agent)
            if agent_name == "NONE":
                return None

            # STEP 8: Return matched agent (or None if agent_name not found)
            return self._agents.get(agent_name)

        except Exception as e:
            # STEP 9: Handle LLM errors gracefully (log and return None)
            self._event_bus.emit(
                EventType.ERROR,
                {"error_type": "llm_classification", "message": str(e)}
            )
            return None  # Fallback to fallback agent or error

    def _extract_tokens(self, response: Any) -> Dict[str, int]:
        """Extract token usage from agent response."""
        # Try to extract token usage from response metadata
        # LangChain responses may have usage_metadata
        try:
            if hasattr(response, 'usage_metadata'):
                usage = response.usage_metadata
                return {
                    "prompt": usage.get("input_tokens", 0),
                    "completion": usage.get("output_tokens", 0),
                    "total": usage.get("total_tokens", 0)
                }
            # Fallback to empty
            return {"prompt": 0, "completion": 0, "total": 0}
        except:
            return {"prompt": 0, "completion": 0, "total": 0}

    def route(self, query: str) -> RouteResult:
        """
        Route query to appropriate agent and execute (main orchestration logic).

        PURPOSE:
            Main entry point for routing queries to specialist agents.
            Like a PLC master controller's main routing loop - decides which station handles each job.

        WHAT THIS DOES (3-Tier Routing):
            1. Try keyword matching first (fastest, deterministic)
            2. If no keyword match, try LLM classification (intelligent)
            3. If still no match, use fallback agent (graceful degradation)
            4. If no fallback, return error (no agent available)
            5. Execute matched agent with full observability
            6. Return structured result with timing, cost, response

        WHY WE NEED THIS:
            - Single entry point for all routing (clean API)
            - Multi-tier routing balances speed vs flexibility
            - Observability enabled throughout (tracing, metrics, costs)
            - Graceful error handling (always returns result, never crashes)

        INPUTS:
            query: User's query string (e.g., "What's my schedule tomorrow?")

        OUTPUTS:
            RouteResult containing:
                - Which agent handled query (agent_name)
                - How routing decision was made (method: keyword/llm/fallback/none)
                - Routing confidence (0.0-1.0)
                - Agent's response (dict or Pydantic model)
                - Any error message
                - Execution duration (milliseconds)
                - Trace ID for observability

        ROUTING PRIORITY:
            1. Keyword (confidence=1.0) - fast, zero cost
            2. LLM (confidence=0.8) - slower, ~$0.001-0.01
            3. Fallback (confidence=0.5) - may not be appropriate
            4. Error (confidence=0.0) - no agent available

        EDGE CASES:
            - Empty query → Keyword match fails, goes to LLM or fallback
            - No agents registered → Returns error
            - Agent execution fails → Returns RouteResult with error field set
            - Observability disabled → Still works, just no tracing/metrics

        TROUBLESHOOTING:
            - Query not routing → Check keywords or agent descriptions
            - Wrong agent routing → Check keyword specificity or LLM prompts
            - Slow routing → Check if keyword matching is working (should be fast)
            - High costs → Too many LLM classifications, add more keywords

        PLC ANALOGY:
            Like PLC master routing loop:
            - query = Incoming part on conveyor
            - Keyword match = Limit switch detecting part type
            - LLM classify = Vision system for complex parts
            - Fallback agent = Default workstation (when type unknown)
            - Execute agent = Send part to appropriate station
            - Return result = Station completion report

        PERFORMANCE:
            - Keyword routing: <1ms, $0
            - LLM routing: 500ms-2s, $0.001-0.01
            - Fallback routing: Variable (depends on fallback agent)
            - Agent execution: Variable (depends on agent complexity)
        """
        # STEP 1: Start timing and tracing (for observability)
        start_time = time.time()
        trace_id = None

        # STEP 2: Start distributed trace if observability enabled (Phase 3+)
        if self._enable_observability:
            trace_id = self.tracer.start_trace(query)

        # STEP 3: Try Tier 1 - Keyword matching (fast, deterministic, zero cost)
        matched = self._match_keywords(query)
        method = "keyword"
        confidence = 1.0  # Keyword match is highly confident

        # STEP 4: Try Tier 2 - LLM classification if no keyword match
        if not matched:
            matched = self._classify_with_llm(query)
            method = "llm"
            confidence = 0.8  # LLM is less certain than keywords

        # STEP 5: Try Tier 3 - Fallback agent if still no match
        if not matched and self._fallback_agent:
            matched = self._agents.get(self._fallback_agent)
            method = "fallback"
            confidence = 0.5  # Fallback may not be appropriate

        # STEP 6: No match at all - return error result
        if not matched:
            if self._enable_observability:
                self.tracer.finish_trace(success=False, error="No agent found")
            return RouteResult(
                agent_name="",
                method="none",
                confidence=0.0,
                error="No agent found for query",
                trace_id=trace_id
            )

        # STEP 7: Emit routing decision event (for monitoring/debugging)
        self._event_bus.emit(
            EventType.ROUTE_DECISION,
            {
                "query": query,
                "matched_agent": matched.name,
                "method": method,
                "confidence": confidence
            }
        )

        # STEP 8: Execute matched agent with full error handling
        try:
            # STEP 8a: Start execution span if observability enabled
            if self._enable_observability:
                span = self.tracer.start_span("agent_execution", agent=matched.name)

            # STEP 8b: Emit agent start event
            self._event_bus.emit(
                EventType.AGENT_START,
                {"query": query},
                agent_name=matched.name
            )

            # STEP 8c: Invoke the agent (main execution)
            raw_response = matched.agent.invoke({"input": query})

            # STEP 8d: Parse response into schema if defined (Pydantic validation)
            parsed_response = self._parse_response(raw_response, matched.agent)

            # STEP 8e: Calculate execution duration
            duration_ms = (time.time() - start_time) * 1000

            # STEP 8f: Extract token usage for cost tracking
            tokens = self._extract_tokens(raw_response)

            # STEP 8g: Record observability metrics (Phase 3+)
            if self._enable_observability:
                span.finish()

                # Record latency and success metrics
                self.metrics.record_request(
                    agent_name=matched.name,
                    duration_ms=duration_ms,
                    success=True,
                    tokens=tokens
                )

                # Record API costs
                agent_metadata = matched.agent.metadata
                self.cost_tracker.record_cost(
                    agent_name=matched.name,
                    provider=agent_metadata.get("llm_provider", "unknown"),
                    model=agent_metadata.get("model", "unknown"),
                    prompt_tokens=tokens.get("prompt", 0),
                    completion_tokens=tokens.get("completion", 0)
                )

                # Finish distributed trace
                self.tracer.finish_trace(
                    success=True,
                    agent_name=matched.name,
                    method=method
                )

            # STEP 8h: Emit agent completion event
            self._event_bus.emit(
                EventType.AGENT_END,
                {"output": str(parsed_response), "duration_ms": duration_ms},
                agent_name=matched.name
            )

            # STEP 8i: Return success result
            return RouteResult(
                agent_name=matched.name,
                method=method,
                confidence=confidence,
                response=parsed_response,
                duration_ms=duration_ms,
                trace_id=trace_id
            )

        except Exception as e:
            # STEP 9: Handle execution errors gracefully
            # STEP 9a: Record error metrics
            if self._enable_observability:
                self.metrics.record_request(
                    agent_name=matched.name,
                    duration_ms=(time.time() - start_time) * 1000,
                    success=False,
                    error_type="agent_execution"
                )
                self.tracer.finish_trace(success=False, error=str(e))

            # STEP 9b: Emit error event
            self._event_bus.emit(
                EventType.ERROR,
                {"error_type": "agent_execution", "message": str(e)},
                agent_name=matched.name
            )

            # STEP 9c: Return error result (don't crash, return structured error)
            return RouteResult(
                agent_name=matched.name,
                method=method,
                confidence=confidence,
                error=str(e),
                trace_id=trace_id
            )

    def route_to(self, agent_name: str, query: str) -> RouteResult:
        """
        Route directly to a specific agent (bypass routing logic).

        PURPOSE:
            Executes a specific agent by name, bypassing the routing decision logic.
            Like manually selecting a PLC workstation instead of using automatic routing.

        WHAT THIS DOES:
            1. Validates agent exists in registry
            2. Executes agent directly (no keyword/LLM matching)
            3. Returns structured result with timing
            4. Emits events for observability

        WHY WE NEED THIS:
            - Testing specific agents in isolation
            - Explicit user choice (e.g., "use calendar agent")
            - Debugging routing issues
            - API endpoints that target specific agents

        INPUTS:
            agent_name: Name of agent to execute (e.g., "calendar_agent")
            query: User's query string

        OUTPUTS:
            RouteResult with method="direct" and confidence=1.0 (or 0.0 if not found)

        EDGE CASES:
            - agent_name not registered → Returns error result
            - Agent execution fails → Returns result with error field set
            - Works even if keywords/LLM would route elsewhere

        TROUBLESHOOTING:
            - "Agent not found" → Check agent name spelling, use list_agents()
            - Agent fails → Check agent is properly configured
            - Observability not working → Only events emitted, no tracing here

        PLC ANALOGY:
            Like manual mode in PLC:
            - Automatic mode = route() uses sensors/vision to decide station
            - Manual mode = route_to() operator selects specific station
            - Still tracks timing and emits events
            - Bypasses normal routing logic

        Examples:
            >>> result = orch.route_to("calendar_agent", "What's my schedule?")
            >>> result = orch.route_to("research_agent", "Find info on Python")
        """
        # STEP 1: Validate agent exists (early exit if not found)
        if agent_name not in self._agents:
            return RouteResult(
                agent_name=agent_name,
                method="direct",
                confidence=0.0,  # Not found = zero confidence
                error=f"Agent '{agent_name}' not found"
            )

        # STEP 2: Get agent registration
        matched = self._agents[agent_name]
        start_time = time.time()

        # STEP 3: Execute agent with error handling
        try:
            # STEP 3a: Emit agent start event
            self._event_bus.emit(
                EventType.AGENT_START,
                {"query": query},
                agent_name=agent_name
            )

            # STEP 3b: Invoke the agent (main execution)
            raw_response = matched.agent.invoke({"input": query})

            # STEP 3c: Parse response into schema if defined
            parsed_response = self._parse_response(raw_response, matched.agent)

            # STEP 3d: Calculate execution duration
            duration_ms = (time.time() - start_time) * 1000

            # STEP 3e: Emit agent completion event
            self._event_bus.emit(
                EventType.AGENT_END,
                {"output": str(parsed_response), "duration_ms": duration_ms},
                agent_name=agent_name
            )

            # STEP 3f: Return success result
            return RouteResult(
                agent_name=agent_name,
                method="direct",
                confidence=1.0,  # Direct routing = full confidence
                response=parsed_response,
                duration_ms=duration_ms
            )

        except Exception as e:
            # STEP 4: Handle execution errors gracefully
            # STEP 4a: Emit error event
            self._event_bus.emit(
                EventType.ERROR,
                {"error_type": "agent_execution", "message": str(e)},
                agent_name=agent_name
            )

            # STEP 4b: Return error result (don't crash, return structured error)
            return RouteResult(
                agent_name=agent_name,
                method="direct",
                confidence=1.0,  # Routing was certain, execution failed
                error=str(e)
            )

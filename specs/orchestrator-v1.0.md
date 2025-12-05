# Orchestrator Specification v1.0

**Spec Type**: Core System Component
**Constitutional Authority**: AGENTS.md Article III (Immutable Architecture)
**Status**: APPROVED
**Created**: 2025-12-05
**Last Updated**: 2025-12-05

---

## 1. PURPOSE

The Orchestrator is a multi-agent routing system that receives user queries and dispatches them to appropriate specialist agents using hybrid routing logic.

**Design Goal**: Route queries to the right agent with >95% accuracy while maintaining <500ms routing overhead.

**Analogy**: Like a PBX phone system - one number routes to many extensions based on intelligent matching.

---

## 2. REQUIREMENTS

### 2.1 Agent Registration (REQ-ORCH-001)

**MUST** support registering specialist agents with metadata:
- Unique name (string identifier)
- Agent instance (LangChain agent executor)
- Keywords list (trigger words, case-insensitive)
- Description (human-readable purpose)
- Priority (integer, higher = higher priority, default 0)
- Fallback flag (boolean, use when nothing matches)

**MUST** reject duplicate agent names with clear error message.

**MUST** allow unregistration of agents by name.

### 2.2 Query Listing (REQ-ORCH-002)

**MUST** provide method to list all registered agent names.

**MUST** provide method to retrieve specific agent by name.

### 2.3 Hybrid Routing Logic (REQ-ORCH-003)

**Routing Priority Order**:
1. Keyword matching (fast, deterministic)
2. LLM classification (flexible, intelligent)
3. Fallback agent (graceful degradation)
4. Error response (no agent available)

**Keyword Matching Rules**:
- Convert query to lowercase
- Check if any registered keyword appears in query
- If multiple agents match, select highest priority
- If priorities equal, select first registered
- Confidence: 1.0 (deterministic match)

**LLM Classification Rules**:
- Only triggered if keyword matching fails
- Requires LLM instance configured
- System prompt lists all available agents with descriptions
- LLM responds with agent name or "NONE"
- Confidence: 0.8 (intelligent but uncertain)

**Fallback Rules**:
- Only triggered if keyword and LLM both fail
- Requires fallback agent configured
- Confidence: 0.5 (last resort)

**Error Handling**:
- If no agent found, return error result (do not raise exception)
- Error message: "No agent found for query"

### 2.4 Agent Execution (REQ-ORCH-004)

**MUST** execute the selected agent with the original query.

**MUST** measure execution time in milliseconds.

**MUST** capture and return agent response.

**MUST** handle agent execution errors gracefully (no crashes).

### 2.5 Direct Routing (REQ-ORCH-005)

**MUST** support bypassing routing logic to call specific agent directly.

**Use Case**: Testing, explicit agent selection, troubleshooting.

**Behavior**: Same as normal routing but skips matching logic.

---

## 3. DATA STRUCTURES

### 3.1 AgentRegistration (Dataclass)

```
name: str               # Unique identifier
agent: Any              # LangChain AgentExecutor
keywords: List[str]     # Lowercase trigger words
description: str        # Human-readable purpose
priority: int           # Tie-breaker (default 0)
```

### 3.2 RouteResult (Dataclass)

```
agent_name: str         # Which agent handled query
method: str             # "keyword" | "llm" | "fallback" | "direct" | "none"
confidence: float       # 0.0-1.0 confidence score
response: Any           # Agent output (or None if error)
error: Optional[str]    # Error message (or None if success)
duration_ms: Optional[float]  # Execution time in milliseconds
```

---

## 4. EVENT SYSTEM INTEGRATION

### 4.1 Event Types (REQ-ORCH-006)

**MUST** emit events at key routing stages:

1. **route_decision** - After routing logic selects agent
   - Data: query, matched_agent, method, confidence

2. **agent_start** - Before invoking agent
   - Data: query
   - Agent: agent_name

3. **agent_end** - After successful agent execution
   - Data: output (string), duration_ms
   - Agent: agent_name

4. **error** - On any error condition
   - Data: error_type (string), message (string)
   - Agent: agent_name (if known)

### 4.2 Event Bus Requirements

**MUST** accept optional EventBus instance at initialization.

**MUST** create default EventBus if none provided.

**MUST** expose EventBus via property for external subscription.

**MUST NOT** crash if event listener throws exception.

---

## 5. PERFORMANCE REQUIREMENTS

### 5.1 Routing Speed (REQ-ORCH-007)

- Keyword matching: <10ms for 100 agents
- LLM classification: <2000ms (depends on LLM provider)
- Total routing overhead: <500ms average

### 5.2 Scalability (REQ-ORCH-008)

- Support 1,000 registered agents without degradation
- Keyword matching remains O(n) linear scan (acceptable for <1000 agents)
- LLM classification independent of agent count (fixed prompt size)

---

## 6. ERROR HANDLING

### 6.1 Required Error Cases (REQ-ORCH-009)

**MUST** handle gracefully:
1. Empty query string → Default to fallback or error
2. No agents registered → Error result
3. LLM unavailable → Fall back to fallback agent
4. LLM returns invalid agent name → Fall back to fallback agent
5. Agent execution fails → Error result with exception message
6. Duplicate agent registration → ValueError with clear message

**MUST NOT**:
- Crash on invalid input
- Hang indefinitely (LLM timeout handled by provider)
- Lose events on listener errors

---

## 7. INPUT VALIDATION

### 7.1 Registration Validation (REQ-ORCH-010)

**name**:
- Not empty string
- Not duplicate of existing agent
- ASCII printable characters only

**keywords**:
- List (can be empty)
- Each keyword is non-empty string
- Converted to lowercase automatically

**priority**:
- Integer
- Can be negative (lower than default)

**description**:
- String (can be empty, will default to "Agent: {name}")

### 7.2 Query Validation (REQ-ORCH-011)

**query**:
- String type (not None)
- Trimmed of whitespace
- If empty after trim → Error result

---

## 8. TESTING REQUIREMENTS

### 8.1 Unit Tests (REQ-ORCH-012)

**MUST** validate:
1. Agent registration succeeds
2. Duplicate registration fails
3. Keyword routing selects correct agent
4. Priority tie-breaking works
5. LLM classification fallback triggers
6. Fallback agent activates when needed
7. Error result on no match
8. Events emitted at correct stages
9. Direct routing bypasses matching
10. Agent execution errors handled
11. Empty query handling

### 8.2 Integration Tests (REQ-ORCH-013)

**MUST** validate:
1. Real LLM classification (with mock LLM)
2. Event history tracking
3. Multiple consecutive queries
4. Agent switching mid-session
5. Performance benchmarks (routing time)

---

## 9. DEPENDENCIES

### 9.1 External Libraries

- **LangChain**: Agent execution (langchain.agents.AgentExecutor)
- **LangChain Core**: LLM interface (langchain_core.language_models.BaseChatModel)
- **LangChain Core**: Messages (langchain_core.messages.{SystemMessage, HumanMessage})

### 9.2 Internal Modules

- **callbacks.py**: EventBus, EventType, Event (see specs/callbacks-v1.0.md)

---

## 10. CONFIGURATION

### 10.1 Initialization Parameters

```python
__init__(
    llm: Optional[BaseChatModel] = None,        # LLM for classification fallback
    event_bus: Optional[EventBus] = None,       # Event system (creates default if None)
    verbose: bool = False                       # Console logging flag
)
```

### 10.2 Verbose Mode Behavior

When `verbose=True`:
- Print registration messages: "[Orchestrator] Registered: {name} (keywords: {keywords})"
- Event bus logs all events to console automatically
- Routing decisions visible in real-time

---

## 11. USAGE EXAMPLES

### 11.1 Basic Registration and Routing

```python
from agent_factory.core import AgentFactory, AgentOrchestrator

# Create factory and agents
factory = AgentFactory()
research_agent = factory.create_agent(role="Research", tools_list=[...])
code_agent = factory.create_agent(role="Coding", tools_list=[...])

# Create orchestrator
orchestrator = factory.create_orchestrator()

# Register agents
orchestrator.register("research", research_agent,
                     keywords=["search", "find", "what is"],
                     description="Answers factual questions")

orchestrator.register("coding", code_agent,
                     keywords=["code", "python", "bug"],
                     description="Helps with programming",
                     is_fallback=True)

# Route query
result = orchestrator.route("What is LangChain?")
print(result.response.get('output'))
```

### 11.2 Event Subscription

```python
# Subscribe to routing decisions
def on_route(event):
    print(f"Routed to: {event.data['matched_agent']}")
    print(f"Method: {event.data['method']}")
    print(f"Confidence: {event.data['confidence']}")

orchestrator.event_bus.on(EventType.ROUTE_DECISION, on_route)

# All routing decisions now logged
orchestrator.route("Write a Python function")
```

### 11.3 Direct Routing (Testing)

```python
# Bypass routing logic for testing
result = orchestrator.route_to("research", "Test query")
assert result.method == "direct"
assert result.confidence == 1.0
```

---

## 12. TROUBLESHOOTING

### Common Issues

**Issue**: Keywords not matching
- Check: Keywords are lowercase in registration
- Check: Query contains exact keyword substring
- Solution: Add more keyword variations

**Issue**: LLM always returns "NONE"
- Check: Agent descriptions are clear and distinct
- Check: LLM has sufficient context
- Solution: Improve descriptions, add examples to prompt

**Issue**: Fallback always triggered
- Check: Keywords list not empty
- Check: LLM is configured and reachable
- Solution: Register agents with better keywords

**Issue**: Events not firing
- Check: Event bus is passed to orchestrator
- Check: Listeners registered before routing
- Solution: Use `orchestrator.event_bus.on()` to subscribe

---

## 13. FUTURE ENHANCEMENTS (Out of Scope v1.0)

- Semantic similarity matching (embeddings)
- Agent load balancing (multiple instances of same agent)
- Query preprocessing (intent extraction, entity recognition)
- Caching layer (repeated queries → cached responses)
- Analytics dashboard (routing success rates, agent performance)
- Multi-turn conversation context (session management)

---

## 14. SPEC COMPLIANCE VALIDATION

### 14.1 Acceptance Criteria

This specification is considered **implemented** when:

1. All REQ-ORCH-* requirements pass unit tests
2. Code contains PLC-style rung annotations referencing this spec
3. factory.py can regenerate orchestrator.py from this spec
4. Integration demo routes 10+ queries with >90% accuracy
5. All troubleshooting scenarios documented and tested

### 14.2 Spec Version History

- **v1.0** (2025-12-05): Initial specification based on Phase 1 prototype

---

**END OF SPECIFICATION**

*This spec is the source of truth for orchestrator behavior. Code is regenerable from this document.*

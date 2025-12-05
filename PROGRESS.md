# PROGRESS.md

## Current Phase: 1 - Orchestration

### Setup
- [ ] Create `agent_factory/core/orchestrator.py`
- [ ] Create `agent_factory/core/callbacks.py`
- [ ] Update `agent_factory/core/__init__.py` with new imports

### Orchestrator Core
- [ ] `AgentOrchestrator` class with `__init__()`
- [ ] `register(name, agent, keywords, priority)` method
- [ ] `list_agents()` returns registered agent names
- [ ] `get_agent(name)` returns specific agent

**CHECKPOINT TEST:**
```bash
poetry run python -c "
from agent_factory.core.orchestrator import AgentOrchestrator
o = AgentOrchestrator()
print('PASS: Orchestrator created')
"
```

### Routing - Keywords
- [ ] `_match_keywords(query)` finds agent by keyword match
- [ ] `route(query)` uses keyword matching first
- [ ] Returns agent response, not just agent

**CHECKPOINT TEST:**
```bash
poetry run python -c "
from agent_factory.core.orchestrator import AgentOrchestrator
from agent_factory.core.agent_factory import AgentFactory

factory = AgentFactory()
agent = factory.create_agent(role='Test', tools_list=[], system_prompt='Say hello')

o = AgentOrchestrator()
o.register('greeter', agent, keywords=['hello', 'hi'])
print('Agents:', o.list_agents())
print('PASS: Registration works')
"
```

### Routing - LLM Fallback
- [ ] `_classify_with_llm(query)` uses LLM when keywords don't match
- [ ] Fallback only triggers when no keyword match
- [ ] Graceful handling when no agent matches

### Callbacks / Events
- [ ] `EventBus` class in `callbacks.py`
- [ ] `emit(event_type, data)` method
- [ ] `on(event_type, callback)` method
- [ ] Orchestrator emits: `agent_start`, `agent_end`, `route_decision`, `error`

**CHECKPOINT TEST:**
```bash
poetry run python -c "
from agent_factory.core.callbacks import EventBus

events = []
bus = EventBus()
bus.on('test', lambda e: events.append(e))
bus.emit('test', {'msg': 'hello'})
print('Events captured:', len(events))
print('PASS: EventBus works')
"
```

### Integration
- [ ] `AgentFactory.create_orchestrator()` method added
- [ ] Orchestrator uses factory's LLM for classification
- [ ] Events integrate with factory

### Demo
- [ ] `examples/orchestrator_demo.py` created
- [ ] Demo registers 2+ agents
- [ ] Demo routes 3+ different queries
- [ ] Demo shows event logging

**FINAL PHASE 1 TEST:**
```bash
poetry run python agent_factory/examples/orchestrator_demo.py
```

### Phase 1 Complete Criteria
- [ ] All checkboxes above are checked
- [ ] All checkpoint tests pass
- [ ] Demo runs without errors
- [ ] Code committed with tag `phase-1-complete`

---

## Phase 2: Structured Outputs
_Not started. Begin after Phase 1 complete._

## Phase 3: Enhanced Observability  
_Not started._

## Phase 4: Deterministic Tools
_Not started._

## Phase 5: Project Twin
_Not started._

## Phase 6: Agent-as-Service
_Not started._

---

## Checkpoints Log

| Tag | Date | What Works |
|-----|------|------------|
| _none yet_ | | |
```

---

Put this file at the root of your Agent Factory project.

**How Claude CLI uses it:**
1. Reads CLAUDE.md → sees "check PROGRESS.md"
2. Finds first unchecked box
3. Implements it
4. Runs checkpoint test
5. If pass → checks box → next
6. If fail → fixes (max 3 tries) → reports if stuck

**How you use it:**
1. Open PROGRESS.md
2. See what's checked vs unchecked
3. Run the checkpoint tests yourself to verify
4. When all boxes checked → phase complete

---

Ready to start? Tell Claude CLI:
```
Read PROGRESS.md. Start with the first unchecked item. 
After completing it, run the checkpoint test and report results.
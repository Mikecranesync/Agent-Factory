# CLAUDE.md

## What This Is

Agent Factory - a framework for building multi-agent AI systems. Part of a larger pipeline that turns ideas into live apps in 24 hours.

**You are building the engine that turns blueprints into working agents.**

---

## Current Focus

> **PHASE 1: ORCHESTRATION**
> 
> Build multi-agent routing. One agent receives query, routes to specialist.

See `docs/PHASE1_SPEC.md` for implementation details.

---

## Execution Rules

### Rule 1: One Thing at a Time
Check `PROGRESS.md` for the current checkbox. Complete it. Validate it. Move to next.

### Rule 2: Always Validate
After ANY change, run:
```bash
poetry run python -c "from agent_factory.core.agent_factory import AgentFactory; print('OK')"
```
If it fails, fix before moving on. Never build on broken code.

### Rule 3: Show Don't Tell
After completing a task, provide:
1. What you built (plain English)
2. How to test it (exact command)
3. Expected output

### Rule 4: Small Commits
After each working feature:
```bash
git add . && git commit -m "CHECKPOINT: [what works]"
```

### Rule 5: Three Strikes
If something fails 3 times, STOP. Report the error. Don't keep trying different approaches - it may be a direction problem, not an execution problem.

### Rule 6: No Refactoring Without Permission
Don't "improve" or "clean up" working code unless explicitly asked. Working > elegant.

### Rule 7: Stay In Scope
If a task requires changing files outside the current phase, ask first.

---

## Architecture Summary
```
agent_factory/
+-- core/
|   +-- agent_factory.py      # Main factory [EXISTS]
|   +-- orchestrator.py       # Routing [PHASE 1]
|   +-- callbacks.py          # Events [PHASE 1]
+-- schemas/                   # [PHASE 2]
+-- tools/                     # [EXISTS]
+-- refs/                      # [PHASE 5]
```

For full architecture, see `docs/ARCHITECTURE.md`.

---

## Reference Documents

| Document | Purpose | When to Read |
|----------|---------|--------------|
| `PROGRESS.md` | Current checklist | Every task |
| `docs/PHASE1_SPEC.md` | Phase 1 implementation details | Building Phase 1 |
| `docs/ARCHITECTURE.md` | Full system design | Need big picture |
| `docs/PATTERNS.md` | Google ADK patterns | Unsure how to structure something |
| `docs/PRODUCTION.md` | Observability, evals, failover | Production readiness |
| `CLAUDE_CODEBASE.md` | Existing code documentation | Need to understand current code |

---

## Standards

- **Python 3.10+**
- **Type hints** on all functions
- **Pydantic** for data models
- **Google ADK patterns** (see `docs/PATTERNS.md`)
- **ASCII-only output** (Windows compatible)

---

## Validation Commands
```bash
# 1. Import check (run after any change)
poetry run python -c "from agent_factory.core.agent_factory import AgentFactory; print('OK')"

# 2. Demo check (run after completing a feature)
poetry run python agent_factory/examples/demo.py

# 3. Test check (run before marking phase complete)
poetry run pytest

# 4. Orchestrator check (Phase 1 specific)
poetry run python -c "from agent_factory.core.orchestrator import AgentOrchestrator; print('OK')"
```

---

## Red Flags - Stop and Report

If you find yourself:
- Refactoring existing working code
- Trying the same fix 3+ times
- Saying "this should work" but it doesn't
- Changing files outside current phase scope
- Unsure why something is failing

**STOP. Report what's happening. Ask for guidance.**

---

## Context for the Human

The project owner is not a coder. When reporting progress:
- Use plain English
- Provide exact test commands they can copy/paste
- Show expected output
- Be honest about uncertainty

---

## Quick Reference: Current Patterns

### Creating Agents (existing)
```python
factory = AgentFactory()
agent = factory.create_agent(role="Name", tools_list=[...], ...)
```

### Creating Tools (existing)
```python
class MyTool(BaseTool):
    name = "my_tool"
    description = "What it does"
    def _run(self, query: str) -> str:
        return result
```

### Orchestrator (building now)
```python
orchestrator = factory.create_orchestrator()
orchestrator.register("name", agent, keywords=["..."])
response = orchestrator.route("user query")
```

---

## Goal

Build agents that are "AI amazing to the customer" - reliable, fast, trustworthy.

The human's apps: **Friday** (voice AI assistant), **Jarvis** (digital ecosystem manager).

---

## When in Doubt

1. Check `PROGRESS.md` for what to do next
2. Check the relevant spec doc for how to do it
3. Validate that it works
4. Commit checkpoint
5. Move to next item

Keep it simple. Keep it working. Keep moving forward.
```

---

Now you need the supporting docs. Here's the file structure:
```
Agent-Factory/
+-- CLAUDE.md              # Meta doc (above) - Claude CLI reads this
+-- PROGRESS.md            # Checklist - tracks what's done
+-- CLAUDE_CODEBASE.md     # Existing - your current code docs
+-- docs/
    +-- ARCHITECTURE.md    # Full architecture + pipeline diagram
    +-- PATTERNS.md        # 8 Google ADK patterns with examples
    +-- PRODUCTION.md      # 4 levels of production readiness
    +-- PHASE1_SPEC.md     # Detailed Phase 1 implementation
    +-- PHASE2_SPEC.md     # (create when ready)
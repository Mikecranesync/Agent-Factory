# SCAFFOLD Orchestrator

**Specification-driven autonomous code generation platform powered by Claude.**

## Overview

The SCAFFOLD orchestrator automates task execution from Backlog.md specifications:
1. Fetches eligible tasks via Backlog.md MCP integration
2. Routes tasks to appropriate handlers (Claude Code CLI or Manual)
3. Executes in isolated git worktrees
4. Creates draft PRs automatically
5. Updates Backlog.md task status

**Vision:** Write task spec → SCAFFOLD executes autonomously → PR opens → Review & merge

---

## Architecture

The orchestrator coordinates 6 core components:

1. **TaskFetcher** - Queries Backlog.md for eligible tasks
2. **TaskRouter** - Routes to ClaudeCodeHandler or ManualActionHandler
3. **WorktreeManager** - Creates isolated git worktrees
4. **SessionManager** - Tracks state + budgets
5. **ResultProcessor** - Creates PRs, updates Backlog.md
6. **ScaffoldOrchestrator** - Main coordination engine

---

## Quick Start


### Basic Usage

```bash
# Run orchestrator (default: max 10 tasks, $5 budget, 4 hours)
poetry run python scripts/autonomous/scaffold_orchestrator.py

# Dry-run mode
DRY_RUN=true poetry run python scripts/autonomous/scaffold_orchestrator.py

# Custom limits
poetry run python scripts/autonomous/scaffold_orchestrator.py   --max-tasks 5   --max-cost 2.0   --max-time-hours 2.0
```

### Programmatic Usage

```python
from agent_factory.scaffold.orchestrator import ScaffoldOrchestrator

orchestrator = ScaffoldOrchestrator(
    max_tasks=10,
    max_cost=5.0,
    max_time_hours=4.0,
    dry_run=False,
    repo_root='.'
)

result = orchestrator.run()
```

---

## Components

### 1. ScaffoldOrchestrator
Main coordination engine with session resumability and error recovery.

### 2. TaskFetcher
Queries Backlog.md via MCP tools, filters by status/dependencies, sorts by priority.

### 3. TaskRouter
Routes tasks: user-action label → ManualHandler, otherwise → ClaudeCodeHandler.

### 4. SessionManager
Manages session lifecycle, integrates WorktreeManager + SafetyMonitor.

### 5. WorktreeManager
Creates worktrees at `../agent-factory-{task-id}`, tracks metadata, enforces limits.

### 6. ResultProcessor
Creates draft PRs, updates Backlog.md status, records cost/duration.

---

## Safety Rails

**Hard Limits (enforced):**
- Cost limit: $5.00 per session
- Time limit: 4 hours wall-clock
- Failure circuit breaker: 3 consecutive failures → STOP

**Per-Task Timeout:** 30 minutes

---

## Workflow

1. Initialize session
2. Fetch eligible tasks from Backlog.md
3. For each task:
   - Check safety limits
   - Create worktree
   - Route to handler
   - Execute
   - Create PR + update Backlog.md
   - Cleanup worktree
4. Generate final summary

---

## Testing

```bash
# All validation tests
poetry run pytest tests/scaffold/test_orchestrator_validation.py -v

# Import tests only
poetry run pytest tests/scaffold/test_orchestrator_validation.py::TestImports -v
```

---

## References

- EPIC Task: task-scaffold-master
- Acceptance Criteria: backlog/tasks/task-scaffold-orchestrator...md
- Test Suite: tests/scaffold/test_orchestrator_validation.py
- CLI: scripts/autonomous/scaffold_orchestrator.py

---

## License

Part of Agent Factory - See root LICENSE file

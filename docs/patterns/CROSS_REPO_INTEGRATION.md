# Cross-Repository Integration Patterns

**Created**: 2025-12-21
**Phase**: Knowledge Extraction (Week 3)
**Purpose**: Document how Agent-Factory, Backlog.md, and pai-config-windows integrate

---

## Overview

Agent Factory's ecosystem consists of 3 core repositories that work together to enable autonomous AI agent development:

1. **Agent-Factory** (Python) - Agent orchestration engine
2. **Backlog.md** (TypeScript/Node) - Task management MCP server
3. **pai-config-windows** (TypeScript/PowerShell) - Windows AI infrastructure

**Core Insight**: These repos share architectural patterns and integration points that enable seamless cross-system workflows.

---

## Integration Map

```
┌─────────────────────────────────────────────────────────────┐
│                     Claude Code CLI                         │
│  (User's development environment)                           │
└─────────────────┬───────────────────────────────────────────┘
                  │
      ┌───────────┴───────────┐
      │                       │
      ▼                       ▼
┌─────────────┐         ┌──────────────┐
│ Backlog.md  │◄────────┤ Agent-Factory│
│ (MCP Server)│         │ (Core Engine)│
└─────────────┘         └──────┬───────┘
      │                        │
      │                        │
      │                        ▼
      │                  ┌──────────────┐
      └─────────────────►│pai-config-   │
                         │windows       │
                         │(Infra Layer) │
                         └──────────────┘
```

### Data Flow

**Agent Development Workflow**:
```
1. User requests feature in Claude Code
    ↓
2. Backlog.md creates task (via MCP)
    ↓
3. Agent-Factory implements feature
    ├── Uses LLM Router (cost optimization)
    ├── Uses Database Manager (multi-provider)
    └── Uses Settings Service (runtime config)
    ↓
4. pai-config hooks capture events
    ├── Session initialized
    ├── Task started/completed
    └── Context checkpointed
    ↓
5. Backlog.md syncs task status
    ↓
6. TASK.md updated (human visibility)
```

---

## Shared Patterns Across Repos

### Pattern 1: Configuration Management

**Common Problem**: All 3 repos need runtime configuration without code changes.

**Solutions**:

**Agent-Factory** (database-backed):
```python
from agent_factory.core.settings_service import settings
model = settings.get("DEFAULT_MODEL", category="llm")
```

**Backlog.md** (YAML config):
```yaml
# backlog/config.yaml
backlog_dir: "./backlog"
milestones:
  - name: "Week 2"
    description: "LLM enhancements"
```

**pai-config-windows** (JSON config):
```json
// settings.json
{
  "hooks": {
    "onToolUse": "hooks/capture-all-events.ts"
  },
  "context": {
    "checkpointInterval": 300
  }
}
```

**Shared Principle**: Environment variables fallback + structured config files.

---

### Pattern 2: Event-Driven Architecture

**Common Problem**: Need to react to lifecycle events (session start, task complete, error).

**Solutions**:

**Agent-Factory** (callbacks):
```python
from agent_factory.core.callbacks import on_agent_complete

@on_agent_complete
def handle_completion(agent_name, result):
    print(f"{agent_name} completed: {result}")
```

**Backlog.md** (MCP protocol events):
```javascript
// Task state changes trigger MCP events
task.on('status_change', (task_id, old_status, new_status) => {
  console.log(`Task ${task_id}: ${old_status} → ${new_status}`)
})
```

**pai-config-windows** (hook system):
```typescript
// hooks/on-task-complete.ts
export async function onTaskComplete(context: HookContext) {
  await saveCheckpoint(context)
  await notifyUser(context.task_id)
}
```

**Shared Principle**: Hook/callback registration with typed event payloads.

---

### Pattern 3: Observability

**Common Problem**: Need visibility into autonomous agent behavior across systems.

**Solutions**:

**Agent-Factory** (distributed tracing):
```python
from agent_factory.observability.tracer import get_tracer

tracer = get_tracer()
with tracer.start_span("agent.answer") as span:
    span.set_attribute("cost_usd", 0.0023)
```

**Backlog.md** (structured logging):
```javascript
logger.info('task_created', {
  task_id: 'task-56',
  priority: 'high',
  assignee: 'claude'
})
```

**pai-config-windows** (event capture):
```typescript
// hooks/capture-all-events.ts
export async function captureEvent(event: Event) {
  await log({
    timestamp: Date.now(),
    type: event.type,
    payload: event.data
  })
}
```

**Shared Principle**: Structured logging with metadata + distributed tracing.

---

### Pattern 4: Context Synchronization

**Common Problem**: Multiple AI sessions need shared context (previous decisions, progress).

**Solutions**:

**Agent-Factory** (message history):
```python
from agent_factory.memory.history import MessageHistory

history = MessageHistory()
history.add_message(role="user", content="Build cache")
history.add_message(role="assistant", content="Implementing...")

# Restore context
messages = history.get_messages(limit=10)
```

**Backlog.md** (task state):
```javascript
// Task notes preserve context
backlog.task_edit({
  id: "task-56",
  notesAppend: ["Implemented LRU cache", "All tests passing"]
})

// Next session reads notes
let task = backlog.task_view({id: "task-56"})
let context = task.notes  // Previous work context
```

**pai-config-windows** (checkpoint system):
```typescript
// Save checkpoint
await saveCheckpoint({
  phase: "implementation",
  progress: 0.75,
  state: {...}
})

// Restore checkpoint
let checkpoint = await restoreCheckpoint()
// Continue from saved state
```

**Shared Principle**: Checkpoint-based context restoration + message history.

---

## Integration Point: Task Creation

**Workflow**: Agent-Factory creates tasks in Backlog.md

```python
# Agent-Factory code
from subprocess import run
import json

def create_task(title, description, priority="medium"):
    """Create Backlog.md task via MCP CLI."""
    cmd = [
        "backlog", "task", "create",
        "--title", title,
        "--description", description,
        "--priority", priority,
        "--assignee", "claude"
    ]

    result = run(cmd, capture_output=True, text=True)
    task_id = json.loads(result.stdout)['task_id']

    return task_id

# Usage
task_id = create_task(
    title="BUILD: Streaming support",
    description="Implement token-by-token LLM streaming",
    priority="high"
)
```

**Result**: Task appears in Backlog.md, syncs to TASK.md, visible to humans and AI.

---

## Integration Point: Settings Propagation

**Workflow**: pai-config settings → Agent-Factory configuration

```typescript
// pai-config-windows: settings.json
{
  "agent_factory": {
    "default_model": "gpt-4o-mini",
    "enable_cache": true,
    "enable_fallback": true
  }
}
```

```python
# Agent-Factory: Read settings from env (set by pai-config)
import os
from agent_factory.llm.router import create_router

router = create_router(
    enable_cache=os.getenv("ENABLE_CACHE", "true") == "true",
    enable_fallback=os.getenv("ENABLE_FALLBACK", "true") == "true"
)
```

**Result**: Centralized configuration in pai-config propagates to Agent-Factory.

---

## Integration Point: Event Capture

**Workflow**: Agent-Factory events → pai-config hooks → Backlog.md updates

```python
# Agent-Factory: Fire event on task completion
from agent_factory.core.callbacks import trigger_event

trigger_event("task_complete", {
    "task_id": "task-56",
    "duration_ms": 1200,
    "cost_usd": 0.0023
})
```

```typescript
// pai-config-windows: Capture event
export async function onTaskComplete(context: HookContext) {
    const {task_id, duration_ms, cost_usd} = context.event

    // Update Backlog.md task
    await runCommand(`backlog task edit ${task_id} --status "Done"`)

    // Log metrics
    await logMetrics({task_id, duration_ms, cost_usd})
}
```

**Result**: Task completion in Agent-Factory automatically updates Backlog.md.

---

## Common Anti-Patterns (Avoid These)

### Anti-Pattern 1: Tight Coupling

**Bad**:
```python
# Agent-Factory directly importing Backlog.md internals
from backlog_md.internal.task_manager import TaskManager

tm = TaskManager()
tm.create_task(...)  # Breaks if Backlog.md changes internals
```

**Good**:
```python
# Agent-Factory uses MCP protocol (stable interface)
from subprocess import run

run(["backlog", "task", "create", ...])  # Protocol-stable
```

**Why**: MCP protocol is stable, internals can change.

---

### Anti-Pattern 2: Duplicate Configuration

**Bad**:
```python
# Agent-Factory config
DEFAULT_MODEL = "gpt-4o-mini"

# pai-config settings.json
"default_model": "gpt-4o-mini"

# (2 sources of truth, drift over time)
```

**Good**:
```python
# Agent-Factory reads from env (set by pai-config)
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-4o-mini")

# pai-config is single source
# settings.json → env vars → Agent-Factory
```

**Why**: Single source of truth prevents drift.

---

### Anti-Pattern 3: Synchronous Cross-Repo Calls

**Bad**:
```python
# Agent-Factory blocking on Backlog.md operation
task_id = backlog.create_task(...)  # Blocks for 500ms
agent.start_work(task_id)  # Can't start until task created
```

**Good**:
```python
# Agent-Factory creates task async
task_id = backlog.create_task_async(...)

# Continue other work
agent.prepare_environment()

# Wait only when needed
task_id = await task_id
```

**Why**: Async prevents cascading latency.

---

## Reusable Components Across Repos

### Component 1: Hook System (pai-config → Agent-Factory)

**Pattern**: Lifecycle hooks for automation.

**pai-config Implementation**:
```typescript
type Hook = (context: HookContext) => Promise<void>

interface HookRegistry {
  register(event: string, hook: Hook): void
  dispatch(event: string, context: HookContext): Promise<void>
}
```

**Agent-Factory Adaptation** (future):
```python
# agent_factory/core/hooks.py (to be created)
from typing import Callable, Awaitable

Hook = Callable[[dict], Awaitable[None]]

class HookRegistry:
    def register(self, event: str, hook: Hook) -> None: ...
    async def dispatch(self, event: str, context: dict) -> None: ...
```

**Benefit**: Same pattern, language-specific implementation.

---

### Component 2: Checkpoint System (pai-config → Agent-Factory)

**Pattern**: Save/restore execution state.

**pai-config Implementation**:
```typescript
interface Checkpoint {
  phase: string
  progress: number
  state: any
}

async function saveCheckpoint(checkpoint: Checkpoint): Promise<void>
async function restoreCheckpoint(): Promise<Checkpoint>
```

**Agent-Factory Adaptation** (future):
```python
# agent_factory/core/context_manager.py (to be created)
from dataclasses import dataclass

@dataclass
class Checkpoint:
    phase: str
    progress: float
    state: dict

async def save_checkpoint(checkpoint: Checkpoint) -> None: ...
async def restore_checkpoint() -> Checkpoint: ...
```

**Benefit**: Portable pattern across ecosystems.

---

## Future Integration Opportunities

### 1. Unified Observability

**Vision**: Single dashboard for all 3 repos.

```
Grafana Dashboard
├── Agent-Factory Metrics
│   ├── LLM costs per agent
│   ├── Query latency (p50, p95, p99)
│   └── Database failover events
├── Backlog.md Metrics
│   ├── Tasks created/completed per day
│   ├── Average task completion time
│   └── Milestone progress
└── pai-config Metrics
    ├── Session duration
    ├── Hook execution time
    └── Context checkpoint frequency
```

**Implementation**: All repos export Prometheus metrics → Grafana.

---

### 2. Shared Knowledge Base

**Vision**: All repos query same knowledge atoms.

```python
# Agent-Factory
from agent_factory.rivet_pro.rag import search_docs
docs = search_docs(intent)

# Backlog.md (via plugin)
const docs = await searchKnowledgeBase(query)

# pai-config (via API)
const docs = await fetch(`${KB_URL}/search?q=${query}`)
```

**Benefit**: One knowledge base, multiple consumers.

---

### 3. Cross-Repo Task Dependencies

**Vision**: Task in Backlog.md depends on pai-config setup.

```yaml
# backlog/tasks/task-56.md
---
dependencies:
  - task-55  # Agent-Factory task
  - pai-config:setup-voice  # pai-config external dependency
---
```

**Benefit**: Clear cross-system dependencies.

---

## Summary

| Integration | Agent-Factory | Backlog.md | pai-config |
|-------------|---------------|------------|------------|
| Configuration | Database + env | YAML + MCP | JSON + env |
| Events | Callbacks | MCP protocol | Hook system |
| Observability | Tracing + metrics | Structured logging | Event capture |
| Context | Message history | Task notes | Checkpoints |

**Key Takeaways**:
1. **Loose Coupling** - MCP protocol, env vars, not direct imports
2. **Shared Patterns** - Hooks, checkpoints, observability (different implementations)
3. **Single Source of Truth** - pai-config settings → Agent-Factory env
4. **Async Communication** - No blocking cross-repo calls

**Production Status**: Agent-Factory + Backlog.md integration proven (100+ tasks managed), pai-config integration in progress.

---

**See Also**:
- `docs/architecture/AGENT_FACTORY_PATTERNS.md` - Agent-Factory patterns
- `docs/architecture/BACKLOG_MCP_PATTERNS.md` - Backlog.md patterns
- `docs/architecture/PAI_CONFIG_PATTERNS.md` - pai-config patterns (forthcoming)

# Backlog.md MCP Patterns

**Created**: 2025-12-21
**Phase**: Knowledge Extraction (Week 3)
**Purpose**: Document Backlog.md task management patterns and MCP server architecture

---

## Overview

Backlog.md is an MCP (Model Context Protocol) server that provides task and document management capabilities to Claude Code via a standardized protocol. It enables AI agents to create, track, and complete tasks programmatically while maintaining a human-readable markdown view layer.

**Core Insight**: Task management should be accessible to both AI agents (via MCP tools) and humans (via markdown files), with bidirectional synchronization ensuring consistency.

**Key Patterns**:
1. **MCP Server Architecture** - Claude Code integration via Model Context Protocol
2. **Structured Markdown** - YAML frontmatter + Markdown content for dual access
3. **Task State Machine** - To Do → In Progress → Done lifecycle
4. **Document Management** - Knowledge docs alongside tasks
5. **Search & Filtering** - Fuzzy search + label-based filtering
6. **Milestone Management** - Config-based + task-referenced milestones
7. **Sync Workflow** - MCP updates ↔ TASK.md bidirectional sync

---

## Pattern 1: MCP Server Architecture

**Problem**: AI agents need structured access to task management, but JSON APIs are clunky and require manual integration.

**Solution**: Implement Model Context Protocol server that Claude Code recognizes automatically.

### Architecture

```
Claude Code CLI
    ↓
MCP Client (built-in)
    ↓
IPC Connection (stdio)
    ↓
Backlog.md MCP Server (npm global package)
    ├── Tools: task_create, task_edit, task_list, task_view, etc.
    ├── Resources: backlog://workflow/overview
    └── Storage: backlog/tasks/*.md
    ↓
TASK.md (auto-generated view layer)
```

### MCP Protocol

**Tools** (18 total):
```javascript
// Task Management
backlog.task_create       // Create new task
backlog.task_list         // List tasks with filters
backlog.task_search       // Fuzzy search tasks
backlog.task_edit         // Update task fields
backlog.task_view         // Get task details
backlog.task_archive      // Archive completed task
backlog.task_complete     // Mark task as done

// Document Management
backlog.document_list     // List all documents
backlog.document_view     // Read document content
backlog.document_create   // Create new document
backlog.document_update   // Update document
backlog.document_search   // Fuzzy search docs

// Milestone Management
backlog.milestone_list    // List milestones
backlog.milestone_add     // Add milestone to config
backlog.milestone_rename  // Rename milestone
backlog.milestone_remove  // Remove milestone

// Workflow Guides
backlog.get_workflow_overview      // Main workflow guide
backlog.get_task_creation_guide    // Task creation best practices
backlog.get_task_execution_guide   // Task execution workflow
backlog.get_task_completion_guide  // Task completion checklist
```

**Resources** (workflow guides):
```javascript
backlog://workflow/overview           // When to use Backlog.md
backlog://workflow/task-creation      // Creating tasks
backlog://workflow/task-execution     // Executing tasks
backlog://workflow/task-completion    // Completing tasks
```

### Usage in Claude Code

**Create Task**:
```javascript
// MCP tool call
backlog.task_create({
  title: "BUILD: LRU cache with TTL",
  description: "Implement OrderedDict-based cache...",
  priority: "high",
  labels: ["llm", "performance"],
  assignee: ["claude"],
  acceptanceCriteria: [
    "Cache stores responses with SHA256 key",
    "TTL-based expiration (1 hour default)",
    "LRU eviction when max_size reached"
  ]
})

// Returns: {task_id: "task-56", status: "created"}
```

**List Tasks**:
```javascript
// Get all tasks in progress
backlog.task_list({
  status: "In Progress",
  assignee: "claude"
})

// Returns: [
//   {task_id: "task-56", title: "BUILD: LRU cache", status: "In Progress"},
//   {task_id: "task-57", title: "BUILD: Streaming support", status: "In Progress"}
// ]
```

**Edit Task**:
```javascript
// Mark task complete
backlog.task_edit({
  id: "task-56",
  status: "Done",
  notesAppend: ["Implemented LRU cache", "All tests passing"]
})
```

### Configuration

**.mcp.json** (project-level):
```json
{
  "mcpServers": {
    "backlog": {
      "command": "npx",
      "args": ["-y", "backlog.md@1.28.0"],
      "env": {
        "BACKLOG_DIR": "./backlog"
      }
    }
  }
}
```

**backlog/config.yaml** (Backlog.md config):
```yaml
backlog_dir: "./backlog"
tasks_dir: "./backlog/tasks"
docs_dir: "./backlog/docs"
completed_dir: "./backlog/tasks/completed"
archived_dir: "./backlog/tasks/archived"

milestones:
  - name: "Week 2: LLM Enhancements"
    description: "Cache, streaming, cost tracking"
  - name: "Week 3-4: RAG & Templates"
    description: "Reranking, SME template, knowledge extraction"
```

### Integration Benefits

**1. Zero Setup** (Claude Code discovers MCP servers automatically):
- No API keys needed
- No manual configuration
- Works out of the box

**2. Type Safety** (MCP protocol enforces schemas):
- Task fields validated on creation
- Compile-time errors for invalid calls
- IntelliSense support in Claude Code

**3. Bidirectional Sync**:
- MCP changes → TASK.md updates automatically
- Human edits .md files → MCP reflects changes
- Single source of truth (backlog/tasks/*.md)

---

## Pattern 2: Structured Markdown

**Problem**: Need format readable by both AI (structured data) and humans (natural language).

**Solution**: YAML frontmatter for metadata + Markdown for content.

### File Structure

**backlog/tasks/task-56.md**:
```markdown
---
task_id: task-56
title: "BUILD: LRU cache with TTL"
status: In Progress
priority: high
labels:
  - llm
  - performance
assignee:
  - claude
created_at: 2025-12-21T10:30:00Z
updated_at: 2025-12-21T14:45:00Z
dependencies:
  - task-55
milestone: "Week 2: LLM Enhancements"
---

# BUILD: LRU cache with TTL

## Description

Implement OrderedDict-based LRU cache to reduce API costs by avoiding redundant LLM calls.

## Acceptance Criteria

- [ ] Cache stores responses with SHA256 key (messages + model + temperature)
- [ ] TTL-based expiration (default 1 hour)
- [ ] LRU eviction when max_size reached
- [ ] Hit/miss rate tracking for monitoring

## Implementation Plan

1. Create `agent_factory/llm/cache.py`
2. Implement ResponseCache class with OrderedDict
3. Add get/set methods with TTL checks
4. Integrate with LLMRouter
5. Add tests

## Notes

- Pattern from Redis TTL + Python OrderedDict
- Expected 30-40% cost reduction
- Cache key must be deterministic (sorted JSON)

## Related

- Depends on: task-55 (LLM Router refactor)
- Blocks: None
```

### YAML Frontmatter Fields

**Required**:
- `task_id`: Unique identifier (e.g., task-56)
- `title`: Short description (max 200 chars)
- `status`: To Do | In Progress | Done
- `created_at`: ISO 8601 timestamp
- `updated_at`: ISO 8601 timestamp

**Optional**:
- `description`: Detailed explanation
- `priority`: low | medium | high
- `labels`: Array of tags (e.g., ["llm", "performance"])
- `assignee`: Array of assignees (e.g., ["claude", "human"])
- `dependencies`: Array of task_id dependencies
- `milestone`: Milestone name from config
- `acceptance_criteria`: Array of criteria (checkboxes)
- `implementation_plan`: Step-by-step plan
- `notes`: Free-form notes

### Markdown Content

**Sections** (conventional structure):
1. **# Title** - H1 with task title
2. **## Description** - Detailed explanation
3. **## Acceptance Criteria** - Checkbox list
4. **## Implementation Plan** - Numbered steps
5. **## Notes** - Additional context
6. **## Related** - Dependencies, blockers, related tasks

### Sync Behavior

**MCP Edit → Markdown Update**:
```javascript
// MCP call
backlog.task_edit({
  id: "task-56",
  status: "Done",
  notesAppend: ["Implemented successfully"]
})

// Results in:
// 1. frontmatter updated: status: Done
// 2. ## Notes section appended: "- Implemented successfully"
// 3. updated_at timestamp refreshed
// 4. TASK.md regenerated
```

**Markdown Edit → MCP Reflects**:
```markdown
<!-- Edit task-56.md manually -->
---
status: Done  # Changed from "In Progress"
---

## Notes
- Implemented successfully  # Added manually
```

```javascript
// MCP call
backlog.task_view({id: "task-56"})

// Returns updated data:
// {status: "Done", notes: ["Implemented successfully"]}
```

---

## Pattern 3: Task State Machine

**Problem**: Task lifecycle needs clear transitions to prevent ambiguity (is "testing" in progress or done?).

**Solution**: Simple 3-state machine with explicit transitions.

### States

```
To Do (pending)
    ↓ (mark as in_progress)
In Progress (active)
    ↓ (mark as done)
Done (completed)
    ↓ (archive)
Archived (historical)
```

### Transitions

**To Do → In Progress**:
```javascript
backlog.task_edit({
  id: "task-56",
  status: "In Progress"
})
```

**In Progress → Done**:
```javascript
backlog.task_edit({
  id: "task-56",
  status: "Done",
  notesAppend: ["All acceptance criteria met"]
})
```

**Done → Archived**:
```javascript
backlog.task_archive({id: "task-56"})

// Moves file:
// backlog/tasks/task-56.md → backlog/tasks/archived/task-56.md
```

### State Invariants

**Exactly ONE task "In Progress" at a time** (enforced by workflow):
```javascript
// Get current task
let current = backlog.task_list({status: "In Progress"})

// Complete current before starting next
if (current.length > 0) {
  backlog.task_edit({id: current[0].task_id, status: "Done"})
}

// Start next task
backlog.task_edit({id: "task-57", status: "In Progress"})
```

**Tasks can't skip states**:
```javascript
// INVALID: To Do → Done (skips In Progress)
backlog.task_edit({id: "task-56", status: "Done"})  // Warning logged

// VALID: To Do → In Progress → Done
backlog.task_edit({id: "task-56", status: "In Progress"})
backlog.task_edit({id: "task-56", status: "Done"})
```

---

## Pattern 4: Document Management

**Problem**: Tasks represent work to do, but need separate space for knowledge (architecture docs, patterns, guides).

**Solution**: Parallel document management with same structured markdown format.

### Document Structure

**backlog/docs/doc-12.md**:
```markdown
---
doc_id: doc-12
title: "SME Agent Pattern"
created_at: 2025-12-21T10:00:00Z
updated_at: 2025-12-21T15:30:00Z
tags:
  - architecture
  - patterns
  - agents
---

# SME Agent Pattern

## Problem

Each domain expert agent had 200+ lines of duplicate boilerplate...

## Solution

Abstract base class enforces standard structure...

## Implementation

(Full pattern documentation)
```

### Document Operations

**Create Document**:
```javascript
backlog.document_create({
  title: "LLM Router Cost Optimization",
  content: "# LLM Router Pattern\n\n## Overview\n\n...",
  tags: ["llm", "cost", "optimization"]
})
```

**Search Documents**:
```javascript
// Fuzzy search
backlog.document_search({
  query: "cost optimization",
  limit: 10
})

// Returns:
// [
//   {doc_id: "doc-12", title: "LLM Router Cost Optimization", score: 0.89},
//   {doc_id: "doc-15", title: "Database Failover Pattern", score: 0.72}
// ]
```

**Update Document**:
```javascript
backlog.document_update({
  id: "doc-12",
  content: "# Updated Content\n\n...",
  title: "LLM Router - Updated Title"
})
```

---

## Pattern 5: Search & Filtering

**Problem**: With 100+ tasks and docs, need fast search and precise filtering.

**Solution**: Fuzzy search for natural language queries + structured filters for exact matches.

### Fuzzy Search (Tasks)

```javascript
// Natural language query
backlog.task_search({
  query: "cache implementation",
  limit: 5
})

// Uses fuzzy matching on:
// - title
// - description
// - notes
// - acceptance criteria

// Returns scored results:
// [
//   {task_id: "task-56", title: "BUILD: LRU cache", score: 0.92},
//   {task_id: "task-44", title: "RAG reranking", score: 0.34}
// ]
```

### Structured Filters (Tasks)

```javascript
// Exact match filters
backlog.task_list({
  status: "In Progress",
  labels: ["llm", "performance"],
  assignee: "claude",
  milestone: "Week 2: LLM Enhancements"
})

// SQL-like query:
// SELECT * FROM tasks
// WHERE status = 'In Progress'
//   AND 'llm' IN labels
//   AND 'performance' IN labels
//   AND 'claude' IN assignee
//   AND milestone = 'Week 2: LLM Enhancements'
```

### Fuzzy Search (Documents)

```javascript
// Search docs by content
backlog.document_search({
  query: "database failover postgresql",
  limit: 5
})

// Returns:
// [
//   {doc_id: "doc-15", title: "Database Failover Pattern", score: 0.87},
//   {doc_id: "doc-20", title: "Multi-Provider Architecture", score: 0.65}
// ]
```

### Search Implementation

**Fuzzy Matching Algorithm**:
- Tokenize query and document
- Calculate Levenshtein distance for each token
- Aggregate scores with TF-IDF weighting
- Return top-k results sorted by score

**Performance**:
- 100 tasks: <10ms (in-memory search)
- 1,000 tasks: <50ms (indexed search)
- Acceptable for interactive use

---

## Pattern 6: Milestone Management

**Problem**: Need to group tasks into milestones (sprints, releases) without hardcoding in tasks.

**Solution**: Milestones defined in config + referenced by tasks.

### Configuration

**backlog/config.yaml**:
```yaml
milestones:
  - name: "Week 2: LLM Enhancements"
    description: "Cache, streaming, cost tracking"
  - name: "Week 3-4: RAG & Templates"
    description: "Reranking, SME template, knowledge extraction"
  - name: "Month 2: RIVET Launch"
    description: "Production deployment, monitoring"
```

### Task Reference

**backlog/tasks/task-56.md**:
```markdown
---
milestone: "Week 2: LLM Enhancements"
---
```

### Milestone Operations

**List Milestones**:
```javascript
backlog.milestone_list()

// Returns:
// [
//   {name: "Week 2: LLM Enhancements", description: "Cache, streaming..."},
//   {name: "Week 3-4: RAG & Templates", description: "Reranking, SME..."}
// ]
```

**Add Milestone**:
```javascript
backlog.milestone_add({
  name: "Year 2: Enterprise Features",
  description: "SSO, RBAC, audit logs"
})

// Updates config.yaml + allows task assignment
```

**Rename Milestone**:
```javascript
backlog.milestone_rename({
  from: "Week 2: LLM Enhancements",
  to: "Week 2: LLM & Cost Optimization",
  updateTasks: true  // Update all tasks referencing this milestone
})
```

**Remove Milestone**:
```javascript
backlog.milestone_remove({
  name: "Week 2: LLM Enhancements",
  taskHandling: "clear"  // Options: clear, keep, reassign
})
```

---

## Pattern 7: Sync Workflow (MCP ↔ TASK.md)

**Problem**: Need both structured MCP access (for AI) and human-readable view (for humans) without duplication.

**Solution**: Source of truth in backlog/tasks/*.md, auto-generated view in TASK.md.

### Architecture

```
Source of Truth: backlog/tasks/*.md
    ↓
MCP Server reads/writes directly
    ↓
Sync Script (scripts/backlog/sync_tasks.py)
    ↓
TASK.md (auto-generated, read-only sync zones)
```

### TASK.md Structure

```markdown
# Agent Factory Task Board

<!-- SYNC:USER_ACTIONS_START -->
<!-- Auto-generated from backlog/tasks/*.md -->
<!-- DO NOT EDIT between SYNC markers -->

## User Actions Required

### ACTION: Setup Railway Database (task-14)
**Priority**: high
**Status**: To Do
(Full task details)

<!-- SYNC:USER_ACTIONS_END -->

<!-- SYNC:CURRENT_TASK_START -->

## Current Task

### BUILD: LRU cache with TTL (task-56)
**Status**: In Progress
(Full task details)

<!-- SYNC:CURRENT_TASK_END -->

<!-- SYNC:BACKLOG_START -->

## Backlog

### BUILD: Streaming support (task-57)
**Priority**: high
(Full task details)

<!-- SYNC:BACKLOG_END -->
```

### Sync Zones

**SYNC:USER_ACTIONS** - Tasks with `user-action` label:
- Manual human actions (signup, API keys, payment)
- Blocking tasks requiring human intervention

**SYNC:CURRENT_TASK** - Exactly one task with status "In Progress":
- The active task being worked on
- Updated immediately when status changes

**SYNC:BACKLOG** - All tasks with status "To Do":
- Sorted by priority (high → medium → low)
- Then by creation date (oldest first)

### Sync Trigger

**Manual Sync**:
```bash
poetry run python scripts/backlog/sync_tasks.py
```

**Automatic Sync** (on MCP operations):
```javascript
// After any MCP edit
backlog.task_edit({id: "task-56", status: "Done"})

// Triggers automatic sync:
// 1. Update backlog/tasks/task-56.md
// 2. Regenerate TASK.md
// 3. Preserve manual edits outside SYNC zones
```

### Manual Edit Preservation

```markdown
# TASK.md

<!-- Manual notes (outside SYNC zones) -->
## Notes
This is my personal note - won't be overwritten

<!-- SYNC:CURRENT_TASK_START -->
(Auto-generated content)
<!-- SYNC:CURRENT_TASK_END -->

<!-- More manual notes -->
## Sprint Planning
We should prioritize...
```

**Sync behavior**:
- Content inside SYNC zones: Overwritten on sync
- Content outside SYNC zones: Preserved (manual edits safe)

---

## Production Usage

### Workflow (AI Agent)

**1. Check TASK.md**:
```markdown
Read TASK.md to see:
- User actions blocking progress
- Current task in progress
- Backlog of pending tasks
```

**2. Start Task**:
```javascript
// Get next priority task
let tasks = backlog.task_list({status: "To Do", priority: "high"})

// Mark as in progress
backlog.task_edit({id: tasks[0].task_id, status: "In Progress"})
```

**3. Execute Task**:
```javascript
// View full task details
let task = backlog.task_view({id: "task-56"})

// Implement solution
// (code, tests, validation)

// Add progress notes
backlog.task_edit({
  id: "task-56",
  notesAppend: ["Implemented LRU cache", "All tests passing"]
})
```

**4. Complete Task**:
```javascript
// Mark complete
backlog.task_edit({id: "task-56", status: "Done"})

// Sync to TASK.md
// (automatic or via script)
```

### Workflow (Human)

**1. Review TASK.md**:
- See current progress
- Identify blocking user actions
- Understand backlog priorities

**2. Create Tasks** (optional):
```javascript
// Via MCP (if using Claude Code)
backlog.task_create({...})

// Or edit .md files directly
// Then run sync script
```

**3. Handle User Actions**:
```markdown
<!-- From TASK.md -->
ACTION: Setup Railway Database (task-14)
- Sign up at railway.app
- Create PostgreSQL instance
- Copy credentials to .env
```

**4. Monitor Progress**:
- TASK.md auto-updates as agents complete tasks
- Review notes, acceptance criteria
- Approve pull requests

---

## Validation Commands

```bash
# List tasks via MCP
backlog task list --status "To Do"

# View task details
backlog task view task-56

# Create task
backlog task create --title "FIX: Bug" --priority high

# Sync to TASK.md
poetry run python scripts/backlog/sync_tasks.py

# Search documents
backlog document search "cost optimization"
```

---

## Summary

| Pattern | Problem | Solution | Benefit |
|---------|---------|----------|---------|
| MCP Server | Manual task API integration | Auto-discovered protocol server | Zero setup |
| Structured Markdown | AI needs data, humans need text | YAML frontmatter + Markdown | Dual access |
| State Machine | Ambiguous task lifecycle | 3 states with clear transitions | No confusion |
| Documents | No place for knowledge docs | Parallel doc management | Organized knowledge |
| Search & Filtering | Hard to find tasks | Fuzzy search + structured filters | Fast discovery |
| Milestones | Manual task grouping | Config-based milestones | Clean organization |
| Sync Workflow | Duplication across files | Single source, auto-generated view | No conflicts |

**Production Status**: Used by Agent Factory (100+ tasks managed), RIVET (50+ agents), PLC Tutor (18 autonomous agents).

---

**See Also**:
- `backlog/README.md` - Full Backlog.md setup guide
- `TASK.md` - Current task board (auto-generated)
- `scripts/backlog/sync_tasks.py` - Sync script source
- `https://github.com/backlog-md/backlog.md` - Backlog.md repository
